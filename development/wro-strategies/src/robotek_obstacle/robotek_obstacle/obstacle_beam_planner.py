"""Beam search over steering sequences (bicycle model) against walls and sign rules."""
import math

import numpy as np

from .obstacle_field import FRONT_L, HALF_W, INNER, OUTER, PILLAR_R, REAR_L, WHEELBASE, track_heading, track_s, unwrap_s


class BeamPlanner:
    """Search steering sequences with the bicycle model against walls and seat rules."""

    def __init__(self, cfg):
        self.cfg = cfg
        # Steering choices for 25 deg, scaled to the configured limit (x1 at 25 deg).
        scale = cfg.steer_limit/0.4363323129985824
        self.choices = np.radians(np.array([-23., -16., -9., -3., 0., 3., 9., 16., 23.]))*scale

    def pose_ok(self, x, y, th, pillars, margin=.02):
        """Footprint clear of walls, island corners and pillars (single pose)."""
        c, s = math.cos(th), math.sin(th)
        for u, v in ((FRONT_L, HALF_W), (FRONT_L, -HALF_W), (-REAR_L, HALF_W), (-REAR_L, -HALF_W)):
            m = max(abs(x+c*u-s*v), abs(y+s*u+c*v))
            if m > OUTER-margin or m < INNER+margin:
                return False
        for px, py in [(INNER, INNER), (INNER, -INNER), (-INNER, INNER), (-INNER, -INNER)]+[(p['x'], p['y']) for p in pillars]:
            u = c*(px-x)+s*(py-y); v = -s*(px-x)+c*(py-y)
            r = 0. if abs(px) == INNER and abs(py) == INNER else PILLAR_R
            if math.hypot(max(u-FRONT_L, -REAR_L-u, 0.), max(abs(v)-HALF_W, 0.))-r < margin:
                return False
        return True

    @staticmethod
    def wrong_side(x, y, th, pillars):
        """Pillars whose radius line the footprint cuts with the car on the wrong side.

        The judge accumulates where the body cuts the inner-to-outer line through the
        pillar while it straddles it (reversing included), so every straddling pose
        must already be on the colour's side, not only the centre when it crosses.
        """
        c, s = math.cos(th), math.sin(th)
        bad = set()
        for p in pillars:
            side = {'green': 1., 'red': -1.}.get(p['color'], 0.)
            if not side:
                continue
            (tx, ty), (nx_, ny_) = p['t'], p['n']
            if not INNER <= nx_*x+ny_*y <= OUTER:
                continue
            a = [tx*(x+c*u-s*v-p['x'])+ty*(y+s*u+c*v-p['y'])
                 for u, v in ((FRONT_L, HALF_W), (FRONT_L, -HALF_W), (-REAR_L, HALF_W), (-REAR_L, -HALF_W))]
            if min(a) <= 0. <= max(a) and side*(-ty*(x-p['x'])+tx*(y-p['y'])) <= 0.:
                bad.add(p['id'])
        return bad

    def plan(self, pose, steer0, pillars, phi0, phi_goal):
        cfg = self.cfg
        ds = cfg.plan_ds
        K = len(self.choices)
        x = np.array([pose[0]]); y = np.array([pose[1]]); th = np.array([pose[2]])
        delta = np.array([steer0]); phi = np.array([phi0]); cost = np.zeros(1)
        parents, states = [], []
        if pillars:
            P = np.array([[p['x'], p['y'], p['t'][0], p['t'][1], p['n'][0], p['n'][1],
                           {'green': 1., 'red': -1.}.get(p['color'], 0.)] for p in pillars])
        corners = np.array([[FRONT_L, HALF_W], [FRONT_L, -HALF_W], [-REAR_L, HALF_W], [-REAR_L, -HALF_W],
                            [0., HALF_W], [0., -HALF_W]])
        island = np.array([[INNER, INNER], [INNER, -INNER], [-INNER, INNER], [-INNER, -INNER]])
        mw, mp = cfg.plan_wall_margin, cfg.plan_pillar_margin
        for depth in range(cfg.plan_steps):
            n = x.size
            X = np.repeat(x, K); Y = np.repeat(y, K); TH = np.repeat(th, K)
            D0 = np.repeat(delta, K); PHI = np.repeat(phi, K); C = np.repeat(cost, K)
            D = np.tile(self.choices, n)
            step_limit = cfg.plan_steer_step*(2. if depth == 0 else 1.)
            ok = np.abs(D-D0) <= step_limit+1e-9
            dth = ds*np.tan(D)/WHEELBASE
            mid = TH+.5*dth
            NX, NY, NTH = X+ds*np.cos(mid), Y+ds*np.sin(mid), TH+dth
            cth, sth = np.cos(NTH), np.sin(NTH)
            # Car outline points.
            cx = NX[:, None]+cth[:, None]*corners[:, 0]-sth[:, None]*corners[:, 1]
            cy = NY[:, None]+sth[:, None]*corners[:, 0]+cth[:, None]*corners[:, 1]
            ok &= np.all(np.maximum(np.abs(cx), np.abs(cy)) <= OUTER-mw, axis=1)
            ok &= np.all(np.maximum(np.abs(cx), np.abs(cy)) >= INNER+mw, axis=1)
            for ix, iy in island:
                u = cth*(ix-NX)+sth*(iy-NY); v = -sth*(ix-NX)+cth*(iy-NY)
                ok &= ~((u <= FRONT_L+mw) & (u >= -REAR_L-mw) & (np.abs(v) <= HALF_W+mw))
            wall_gap = np.minimum(OUTER-np.max(np.maximum(np.abs(cx), np.abs(cy)), axis=1),
                                  np.min(np.maximum(np.abs(cx), np.abs(cy)), axis=1)-INNER)
            C = C+cfg.plan_wall_cost*np.maximum(0., cfg.plan_soft-wall_gap)**2
            if pillars:
                for px, py, tx, ty, nx_, ny_, side in P:
                    u = cth*(px-NX)+sth*(py-NY); v = -sth*(px-NX)+cth*(py-NY)
                    gap = np.hypot(np.maximum(np.maximum(u-FRONT_L, -REAR_L-u), 0.),
                                   np.maximum(np.abs(v)-HALF_W, 0.))-PILLAR_R
                    ok &= gap >= mp
                    C = C+cfg.plan_pillar_cost*np.maximum(0., mp+cfg.plan_soft-gap)**2
                    # Radius rule: crossing the inner-to-outer line through the seat.
                    a0 = tx*(X-px)+ty*(Y-py); a1 = tx*(NX-px)+ty*(NY-py)
                    outward = nx_*NX+ny_*NY
                    crossing = (a0 < 0.) & (a1 >= 0.) & (outward >= INNER) & (outward <= OUTER)
                    lateral = -ty*(NX-px)+tx*(NY-py)  # + is left of travel (inner side)
                    ok &= ~crossing | ((side != 0.) & (side*lateral > 0.))
                    if side != 0.:
                        # Footprint straddling the radius line must be on the right side
                        # (already wrong: no forward plan -> blocked -> reverse out).
                        prog = tx*(cx-px)+ty*(cy-py)
                        straddle = (prog.min(axis=1) <= 0.) & (prog.max(axis=1) >= 0.) & (outward >= INNER) & (outward <= OUTER)
                        ok &= ~straddle | (side*lateral > 0.)
                    approaching = (a1 < 0.) & (a1 > -cfg.plan_side_window) & (outward >= INNER) & (outward <= OUTER)
                    if side != 0.:
                        # Change lane early: penalize the wrong side while approaching.
                        wrong = np.maximum(0., HALF_W+PILLAR_R+mp-side*lateral)
                        C = C+cfg.plan_side_cost*approaching*(1.+a1/cfg.plan_side_window)*wrong**2
                    else:
                        # Unknown colour: reward keeping it in the camera's view.
                        seen = (u > .15) & (np.abs(np.arctan2(v, u)) < .42) & (u*u+v*v < 4.)
                        C = C-cfg.plan_view_gain*ds*seen
                        # Keep both sides reachable: approach in line with the pillar.
                        C = C+cfg.plan_unknown_cost*approaching*lateral**2
            NPHI = unwrap_s(PHI, track_s(NX, NY))
            C = C+cfg.plan_steer_cost*D**2+cfg.plan_rate_cost*(D-D0)**2
            idx = np.nonzero(ok)[0]
            if idx.size == 0:
                break
            score = cfg.plan_progress_gain*np.minimum(NPHI[idx], phi_goal)-C[idx]
            order = idx[np.argsort(-score)]
            # Diversity: best node per (x, y, heading) cell, as in hybrid A*.
            cells = np.stack([np.round(NX[order]/cfg.plan_cell), np.round(NY[order]/cfg.plan_cell),
                              np.round(NTH[order]/.2)], axis=1)
            _, first = np.unique(cells, axis=0, return_index=True)
            keep = order[np.sort(first)[:cfg.plan_beam]]
            parents.append(keep//K)
            states.append((NX[keep], NY[keep], NTH[keep], D[keep]))
            x, y, th, delta, phi, cost = NX[keep], NY[keep], NTH[keep], D[keep], NPHI[keep], C[keep]
        if not states:
            return None
        # Terminal cost: end aligned with the lane so the next turn stays feasible
        # beyond the horizon (cutting corners diagonally leads to dead ends).
        misalign = np.arctan2(np.sin(th-track_heading(x, y)), np.cos(th-track_heading(x, y)))
        if len(states) == cfg.plan_steps:
            cost = cost+cfg.plan_terminal_heading_cost*misalign**2
        best = int(np.argmax(cfg.plan_progress_gain*np.minimum(phi, phi_goal)-cost))
        self.last_progress = float(phi[best])
        path = []
        for depth in range(len(states)-1, -1, -1):
            sx, sy, sth, sd = states[depth]
            path.append((sx[best], sy[best], sth[best], sd[best]))
            best = int(parents[depth][best])
        return np.array(path[::-1])
