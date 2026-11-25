"""Line through a corner of the Obstacle v2 lane: straight, one left arc, straight.

Worked in the frame of the first corner (bottom straight -> right straight, island corner at
(0.5, -0.5)); every corner is that one turned, so the result is given in lane coordinates
(progress from the corner start, lateral offset) and applies to all of them.

The line holds offset ``d_a`` on the straight before the corner, turns left on an arc of radius
``r`` and holds ``d_b`` on the straight after it. ``plan`` searches those three numbers for the
largest clearance to the signs at the corner (the last seat of the first straight and the first
seat of the next one), the island and the outer wall, with the car's outline and the side each
sign must be passed on. The result depends only on the signs, so it is cached.
"""
import math
from functools import lru_cache

import numpy as np

from robotek_common.vehicle import OUTLINE_FRONT, OUTLINE_HALF_WIDTH, OUTLINE_REAR, WHEELBASE

SIGN_HALF = 0.025           # m, half of a 50 mm sign
STEP = 0.02                 # m between path samples
RADII = (0.5, 0.6, 0.75)     # m; tighter arcs leave the tracker no steering to correct with
OFFSET_LIMIT = 0.36         # m from the lane centre
OFFSET_GRID = 0.02          # m between candidate offsets
FREE_SHIFT = 0.1            # m an end without a sign may move from the neighbouring sign's offset
ENOUGH = 0.11               # m; past this clearance the line stays near the centre
BEFORE = 0.15               # track units before the corner the plan starts (a sign's hold)
AFTER = 0.15                # track units into the next straight it ends at the latest


def _outline():
    """Perimeter points of the car in base_link (x ahead, y left)."""
    xs = np.linspace(-OUTLINE_REAR, OUTLINE_FRONT, 7)
    ys = np.linspace(-OUTLINE_HALF_WIDTH, OUTLINE_HALF_WIDTH, 3)
    points = [(x, y) for x in xs for y in (ys[0], ys[-1])] + [(x, y) for x in (xs[0], xs[-1]) for y in ys[1:-1]]
    return np.array(points)


OUTLINE = _outline()
CORNERS = np.array([(OUTLINE_FRONT, OUTLINE_HALF_WIDTH), (-OUTLINE_REAR, OUTLINE_HALF_WIDTH),
                    (-OUTLINE_REAR, -OUTLINE_HALF_WIDTH), (OUTLINE_FRONT, -OUTLINE_HALF_WIDTH)])


def path(d_a, d_b, r):
    """Samples (x, y, body yaw) of the line in the first corner's frame, or None if it does not fit."""
    y_a, x_b = -1.0 + d_a, 1.0 - d_b
    cx, cy = x_b - r, y_a + r
    x_start = min(0.5 - BEFORE, cx)
    y_end = max(-0.5 + AFTER, cy)
    if x_start < -0.3 or cy > 0.3:
        return None
    # base_link sits half a wheelbase ahead of the rear axle: on an arc its body points
    # slightly outside the tangent.
    slip = math.atan2(WHEELBASE / 2.0, math.sqrt(max(r * r - (WHEELBASE / 2.0) ** 2, 1e-9)))
    line_a = np.arange(x_start, cx, STEP)
    angles = np.arange(-math.pi / 2, 0.0, STEP / r)
    line_b = np.arange(cy, y_end + 1e-9, STEP)
    x = np.concatenate([line_a, cx + r * np.cos(angles), np.full(line_b.size, x_b)])
    y = np.concatenate([np.full(line_a.size, y_a), cy + r * np.sin(angles), line_b])
    yaw = np.concatenate([np.zeros(line_a.size), angles + math.pi / 2 - slip, np.full(line_b.size, math.pi / 2)])
    return x, y, yaw


def _box_distance(px, py, bx, by):
    dx = np.maximum(np.abs(px - bx) - SIGN_HALF, 0.0)
    dy = np.maximum(np.abs(py - by) - SIGN_HALF, 0.0)
    return np.hypot(dx, dy)


def clearance(samples, sign_a, sign_b):
    """Smallest distance (m) of the outline to the signs, the island and the outer wall along the
    samples; negative when a sign is passed on the wrong side. ``sign_a``/``sign_b`` are
    (lateral, colour) or None."""
    x, y, yaw = samples
    c, s = np.cos(yaw)[:, None], np.sin(yaw)[:, None]
    px = x[:, None] + c * OUTLINE[:, 0] - s * OUTLINE[:, 1]
    py = y[:, None] + s * OUTLINE[:, 0] + c * OUTLINE[:, 1]
    qx = x[:, None] + c * CORNERS[:, 0] - s * CORNERS[:, 1]
    qy = y[:, None] + s * CORNERS[:, 0] + c * CORNERS[:, 1]
    island = np.maximum(np.abs(px), np.abs(py)) - 0.5
    outer = 1.5 - np.maximum(np.abs(px), np.abs(py))
    worst = min(float(island.min()), float(outer.min()))
    signs = []
    if sign_a is not None:
        # Last seat of the bottom straight: along x, lateral (to the island) along y.
        signs.append((sign_a, 0.5, -1.0 + sign_a[0], qx - 0.5, qy + 1.0))
    if sign_b is not None:
        # First seat of the right straight: along y, lateral along -x.
        signs.append((sign_b, 1.0 - sign_b[0], -0.5, qy + 0.5, 1.0 - qx))
    for (lateral, colour), bx, by, along, side in signs:
        worst = min(worst, float(_box_distance(px, py, bx, by).min()))
        if colour is None:
            continue
        low, high = _cut(along, side)
        if low.size:
            margin = lateral - SIGN_HALF - high.max() if colour == 'red' else low.min() - lateral - SIGN_HALF
            worst = min(worst, float(margin))
    return worst


def _cut(along, side):
    """Lateral interval where each sample's outline cuts the sign's line (along = 0), as the
    judge measures the side; only samples that straddle the line."""
    a0, a1 = along, np.roll(along, -1, axis=1)
    s0, s1 = side, np.roll(side, -1, axis=1)
    hits = (a0 <= 0.0) != (a1 <= 0.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        cut = np.where(hits, s0 + (s1 - s0) * a0 / (a0 - a1), np.nan)
    rows = hits.any(axis=1)
    return np.nanmin(cut[rows], axis=1), np.nanmax(cut[rows], axis=1)


def _band(sign, fixed):
    """Candidate offsets for the straight next to a corner."""
    if sign is None:
        # No sign at this end of the corner: the line may leave the neighbouring sign's offset.
        return [d for d in np.arange(fixed - FREE_SHIFT, fixed + FREE_SHIFT + 1e-9, 0.05)
                if abs(d) <= 0.3]
    if sign[1] is None:
        return [fixed]
    lateral, colour = sign
    edge = SIGN_HALF + OUTLINE_HALF_WIDTH
    low, high = (-OFFSET_LIMIT, lateral - edge) if colour == 'red' else (lateral + edge, OFFSET_LIMIT)
    return list(np.arange(low, high + 1e-9, OFFSET_GRID)) or [fixed]


def _offsets(sign, fixed, low):
    """Candidate offsets for one end, at or above ``low``."""
    return [d for d in _band(sign, fixed) if d >= low] or [max(fixed, low)]


def _score(gap, d_a, d_b, pref_a, pref_b, r):
    """Enough clearance: stay near the lane centre (shorter shifts, signs stay in the camera's
    view), then prefer a wide arc. Otherwise: the most clearance."""
    if gap >= ENOUGH:
        return (1, -abs(d_a - pref_a) - abs(d_b - pref_b), r)
    return (0, gap, r)


@lru_cache(maxsize=256)
def plan(sign_a, sign_b, fixed_a, fixed_b, low_a=-1.0, low_b=-1.0):
    """Best (clearance, d_a, d_b, r) for a corner. ``fixed_*`` is the offset used on a side
    without a sign of known colour (the neighbouring sign's offset, or the default);
    ``low_*`` the smallest offset allowed on that side (beside the parking lot)."""
    best = None
    # A free end stays near its neighbour's offset; an end with a sign near the centre.
    pref_a = fixed_a if sign_a is None else 0.0
    pref_b = fixed_b if sign_b is None else 0.0
    for r in RADII:
        for d_a in _offsets(sign_a, fixed_a, low_a):
            for d_b in _offsets(sign_b, fixed_b, low_b):
                samples = path(d_a, d_b, r)
                if samples is None:
                    continue
                gap = clearance(samples, sign_a, sign_b)
                score = _score(gap, d_a, d_b, pref_a, pref_b, r)
                if best is None or score > best[0]:
                    best = (score, gap, float(d_a), float(d_b), r)
    if best is None:
        return None
    return best[1:]


@lru_cache(maxsize=256)
def knots(d_a, d_b, r):
    """The line as (progress from the corner start, lateral offset) pairs."""
    x, y, _ = path(d_a, d_b, r)
    out = []
    for px, py in zip(x, y):
        if px <= 0.5:
            out.append((px - 0.5, py + 1.0))
        elif py >= -0.5:
            out.append((1.0 + py + 0.5, 1.0 - px))
        else:
            angle = math.atan2(py + 0.5, px - 0.5)
            out.append((1.0 + angle / (math.pi / 2), 0.5 - math.hypot(px - 0.5, py + 0.5)))
    return tuple(out)
