#!/usr/bin/env python3
"""Precompute the Obstacle v3 corner lines (corner.plan) for every argument the mission can ask for.

    python3 tools/build_corner_table.py          # writes src/robotek_obstacle/robotek_obstacle/v3/corner_table.py

corner.plan drives each candidate through the simulated tracker (11-70 ms on the remote's Ryzen; several
times that on the car's Pi), so the car looks the result up instead. Its arguments are discrete: signs sit
at +-0.1 m with a colour or none, a free end keeps the side offset of its neighbouring sign (rounded to
1 cm) or 0, the neighbour itself when it is on the adjacent seat, and the lot limit on one side or none.
Anything else (another pillar_clearance) falls back to computing it. Run it again after changing
corner.py or the v3 mission's side offsets; test_v3_corner_table checks a sample against corner._choose.

Corners whose best straight-arc-straight line leaves less than SEARCH_BELOW of driven clearance (the S
corners: a sign passed on the island side, the next one on the outer side) also get a searched line:
a weighted A* over forward arcs of radius >= 0.5 m (what the tracker can follow) with the signs, the
signs on the adjacent seats and the lot limits as obstacles, plus a virtual wall on each known sign's
wrong side. The searched line is driven through the same simulated tracker and kept only if it beats
the family by MIN_GAIN.
"""
import heapq
import math
import itertools
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for package in ('robotek_obstacle', 'robotek_common'):
    sys.path.insert(0, str(ROOT/'src'/package))
OUT = ROOT/'src/robotek_obstacle/robotek_obstacle/v3/corner_table.py'


def arguments():
    """Every corner.plan argument tuple the v3 mission can produce with its default parameters."""
    from robotek_obstacle.v3.mission import LOT_OFFSET, Mission
    mission = Mission()
    ends = []
    signs = list(itertools.product((0.1, -0.1), ('red', 'green', None)))
    for sign in signs:
        offset = round(mission._side_offset(*sign), 2)
        ends.append((sign, offset, (False,)))        # a sign on the corner's own seat
        ends.append((None, offset, (sign,)))         # none there; this one on the adjacent seat
    for fixed in sorted({round(mission._side_offset(*sign), 2) for sign in signs}) + [0.0]:
        ends.append((None, fixed, (False,)))         # the neighbour further away, or none
    lots = ((-1.0, -1.0), (LOT_OFFSET, -1.0), (-1.0, LOT_OFFSET))
    for (sa, fa, pa), (sb, fb, pb), (la, lb) in itertools.product(ends, ends, lots):
        for pin_a, pin_b in itertools.product(pa, pb):
            yield (sa, sb, fa, fb, la, lb, pin_a, pin_b)


SEARCH_BELOW = 0.035     # m of driven clearance under which a corner also gets a searched line
MIN_GAIN = 0.005         # m a searched line must add over the family's line
MARGINS = (0.05, 0.04, 0.03)   # m kept from obstacles by the search, widest first
STEP = 0.04              # m per searched arc
LIMIT = 60000            # expansions per search
SIGN = 0.025


def _obstacles(args):
    """Boxes (xmin, xmax, ymin, ymax) in the corner frame: each sign, a wall on its wrong side when
    its colour is known, and the lot limits' line beside the lot."""
    sign_a, sign_b, _, _, low_a, low_b, pin_a, pin_b = args
    boxes = []

    def bottom(sign, x):        # a sign on the straight before the corner: lateral along +y
        lateral, colour = sign
        y = -1.0 + lateral
        boxes.append((x - SIGN, x + SIGN, y - SIGN, y + SIGN))
        if colour == 'green':   # pass on the island side: the outer side is closed
            boxes.append((x - SIGN, x + SIGN, -1.5, y))
        elif colour == 'red':
            boxes.append((x - SIGN, x + SIGN, y, -0.5))

    def right(sign, y):         # a sign on the straight after the corner: lateral along -x
        lateral, colour = sign
        x = 1.0 - lateral
        boxes.append((x - SIGN, x + SIGN, y - SIGN, y + SIGN))
        if colour == 'green':
            boxes.append((x, 1.5, y - SIGN, y + SIGN))
        elif colour == 'red':
            boxes.append((0.5, x, y - SIGN, y + SIGN))

    for sign, x in ((sign_a, 0.5), (pin_a or None, 0.0)):
        if sign:
            bottom(sign, x)
    for sign, y in ((sign_b, -0.5), (pin_b or None, 0.0)):
        if sign:
            right(sign, y)
    if low_a > -1.0:
        boxes.append((0.11, 0.50, -1.5, -1.3))
    if low_b > -1.0:
        boxes.append((1.3, 1.5, -0.50, -0.11))
    return boxes


def _gap(pose, boxes):
    import numpy as np
    from robotek_obstacle.v3 import corner
    x, y, th = pose
    c, s = math.cos(th), math.sin(th)
    px = x + c * corner.OUTLINE[:, 0] - s * corner.OUTLINE[:, 1]
    py = y + s * corner.OUTLINE[:, 0] + c * corner.OUTLINE[:, 1]
    ring = np.maximum(np.abs(px), np.abs(py))
    gap = min(float((ring - 0.5).min()), float((1.5 - ring).min()))
    for x0, x1, y0, y1 in boxes:
        dx = np.maximum(np.maximum(x0 - px, px - x1), 0.0)
        dy = np.maximum(np.maximum(y0 - py, py - y1), 0.0)
        gap = min(gap, float(np.hypot(dx, dy).min()))
    return gap


def _search(start, goal, boxes, margin):
    """Forward arcs (radius 0.5 m left/right, or straight) from start to the goal box -> samples."""
    from robotek_obstacle.obstacle_parking import move
    steer = math.atan(0.1188 / 0.5)
    turn = lambda a: math.atan2(math.sin(a), math.cos(a))
    h = lambda p: math.hypot(p[0] - goal[0], max(goal[1] - p[1], 0.0)) + 0.3 * abs(turn(p[2] - math.pi / 2))
    queue = [(h(start), 0.0, start, None, None)]
    parents, seen, count = {}, {}, 0
    while queue and count < LIMIT:
        _, cost, pose, last, parent = heapq.heappop(queue)
        count += 1
        cell = (round(pose[0] / 0.02), round(pose[1] / 0.02), round(pose[2] / math.radians(5)))
        if seen.get(cell, math.inf) <= cost:
            continue
        seen[cell] = cost
        parents[cell] = (parent, pose)
        if pose[1] >= goal[1] and abs(pose[0] - goal[0]) < 0.05 and abs(turn(pose[2] - math.pi / 2)) < math.radians(8):
            points, node = [], cell
            while node is not None:
                parent, p = parents[node]
                points.append(p)
                node = parent
            return points[::-1]
        for st in (-steer, 0.0, steer):
            q, ok = pose, True
            for _ in range(4):
                q = move(*q, st, STEP / 4)
                if _gap(q, boxes) < margin:
                    ok = False
                    break
            if ok:
                extra = 0.02 if last is not None and last != st else 0.0
                heapq.heappush(queue, (cost + STEP + extra + h(q), cost + STEP + extra, q, st, cell))
    return None


def _searched(args):
    """Searched lines of a corner, as corner._tracked rows (driven clearance first)."""
    from robotek_obstacle.v3 import corner
    prefs, entry, leave, lot, near = corner.context(args)
    fixed_a, fixed_b = args[2], args[3]
    x0 = entry[1] if entry else 0.15
    y_goal = leave[1] if leave else -0.3
    start, goal = (x0, -1.0 + fixed_a, 0.0), (1.0 - fixed_b, y_goal)
    boxes = _obstacles(args)
    rows = []
    for margin in MARGINS:
        points = _search(start, goal, boxes, margin)
        if points:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            line = tuple(corner.to_knots(xs, ys)[::2])
            spec = (('k', tuple((float(u), float(d)) for u, d in line)),)
            rows += corner._tracked([(None, None) + spec], args[0], args[1], (entry, leave), prefs, lot, None, near)
    return rows


def _solve(args):
    from robotek_obstacle.v3 import corner
    family = corner._choose(args)
    if family is None or family[0] >= SEARCH_BELOW:
        return args, family
    rows = _searched(args)
    found = corner.best(rows)[0:] if rows else None
    if found is not None and found[0] >= family[0] + MIN_GAIN:
        return args, found
    return args, family


def main():
    jobs = sorted(set(arguments()), key=repr)
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 2)) as pool:
        results = list(pool.map(_solve, jobs, chunksize=8))
    lines = ['"""Generated by tools/build_corner_table.py: corner.plan for every argument the v3 mission asks for.',
             '', 'Do not edit; run the tool again after changing corner.py or the mission\'s side offsets."""',
             'TABLE = {']
    for args, result in results:
        if result is None or len(result) == 2:
            value = result                       # None, or (clearance, ('k', knots)) of a searched line
        else:
            value = tuple(float(v) for v in result)   # repr round-trips
        lines.append(f'    {args!r}: {value!r},')
    lines.append('}')
    OUT.write_text('\n'.join(lines) + '\n')
    searched = sum(1 for _, r in results if r is not None and len(r) == 2)
    print(f'{len(results)} corners ({searched} with a searched line) -> {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
