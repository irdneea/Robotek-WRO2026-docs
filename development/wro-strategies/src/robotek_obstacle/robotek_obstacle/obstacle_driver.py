"""Map-based Obstacle driving: owns pose, map and path and turns them into commands.

Localization (obstacle_localizer), sign map (obstacle_seat_map) and search
(obstacle_beam_planner) run in the mirrored track frame of obstacle_field. No
simulator pose is used.
"""
import math
import time

import numpy as np

from .obstacle_beam_planner import BeamPlanner
from .obstacle_field import (HALF_W, INNER, LIDAR_OFFSET_X, OUTER, REAR_L, SWAP, WHEELBASE, scan_points,
                             track_s, unwrap_s, wrap)
from .obstacle_localizer import Localizer
from .obstacle_perception import scan_clusters
from .obstacle_seat_map import SeatMap


class ObstacleDriver:
    """Owns pose, map and path; returns (speed, steer, state) in the real frame."""

    def __init__(self, cfg, sign, heading_abs):
        self.cfg = cfg
        self.sign = sign  # +1 ccw, -1 cw (mirror)
        self.yaw0 = heading_abs
        self.loc = Localizer()
        self.map = SeatMap()
        self.planner = BeamPlanner(cfg)
        self.phi = None
        self.phi_goal = None
        self.path = None
        self.steer = 0.
        self.speed = 0.
        self.state = 'PLAN_INIT'
        self.blocked_since = None
        self.recover_until = None
        self.recover_steer = 0.
        self.plan_ms = math.nan
        self._last_plan = -math.inf
        self._pending = 0.

    # ---------------------------------------------------------------- frames
    def heading(self, yaw_abs):
        return self.sign*wrap(yaw_abs-self.yaw0)+self.loc_th0

    def pose(self):
        return (self.loc.x, self.loc.y, self.loc.th)

    # ---------------------------------------------------------------- inputs
    def on_scan(self, scan):
        bx, by = scan_points(scan, self.sign)
        if not self.loc.ready:
            self.loc_th0 = 0.
            self.loc.initialize(bx, by, 0.)
            self.loc_th0 = self.loc.th
            self.phi = float(track_s(self.loc.x, self.loc.y))
            # Stop point in the start straight after the laps (8 units per lap).
            self.phi_goal = self.cfg.plan_stop_x+INNER+8.*self.cfg.laps
            self.state = 'PLAN'
            return
        before = self.loc.th
        self.loc.correct(bx, by, self.cfg.plan_loc_gain)
        # Keep the heading correction: predict() rebuilds th from the IMU.
        self.loc_th0 += wrap(self.loc.th-before)
        pose = self.pose()
        # Self returns (chassis/camera mount, ~6 cm from the lidar) are not pillars.
        clusters = [(c['x'], self.sign*c['y']) for c in scan_clusters(scan)
                    if math.hypot(c['x']-LIDAR_OFFSET_X, c['y']) > .16]
        self.map.lidar(clusters, pose)

    def on_observations(self, observations):
        if not self.loc.ready:
            return
        obs = [(o['x'], self.sign*o['y'], o['color'] if self.sign > 0 else SWAP[o['color']])
               for o in observations]
        self.map.camera(obs, self.pose())

    # ------------------------------------------------------------- planning
    def _replan(self, now):
        """Replan every plan_period of simulated time, inside the control step (reproducible)."""
        if self.state not in ('PLAN', 'FINISH') or now-self._last_plan < self.cfg.plan_period:
            return
        self._last_plan = now
        t0 = time.time()
        self.path = self.planner.plan(self.pose(), self.steer, self.map.pillars(), self.phi, self.phi_goal)
        self.plan_ms = 1000*(time.time()-t0)  # wall time, diagnostics only

    # -------------------------------------------------------------- control
    def track(self, yaw_abs, distance):
        """Dead-reckon the pose between wall fits; False until the first fit.

        distance: travelled since the previous call (m, unsigned; the sign comes from
        the last commanded speed, self.speed). Distance before the first wall fit is
        applied on the first localized call.
        """
        self._pending += distance
        if not self.loc.ready:
            return False
        distance, self._pending = self._pending, 0.
        if self.speed < 0:
            distance = -distance
        self.loc.predict(distance, self.heading(yaw_abs))
        pose = self.pose()
        self.phi = float(unwrap_s(self.phi, track_s(pose[0], pose[1])))
        return True

    def step(self, now, yaw_abs, distance):
        """distance: travelled since the previous step (m, unsigned; sign from the last command)."""
        cfg = self.cfg
        if not self.track(yaw_abs, distance):
            return 0., 0., self.state
        pose = self.pose()
        self._replan(now)
        path = self.path
        remaining = self.phi_goal-self.phi
        if self.state == 'DONE':
            return 0., 0., self.state
        if remaining <= 0.:
            self.state = 'DONE'
            self.speed = 0.
            return 0., 0., self.state
        if remaining < self.cfg.plan_finish_zone:
            self.state = 'FINISH'
        x, y, th = pose
        if self.recover_until is not None:
            if now < self.recover_until and self._reverse_clear(pose):
                self.speed = -cfg.recover_speed
                self.steer = self.recover_steer
                return -cfg.recover_speed, self.sign*self.recover_steer, 'PLAN_RECOVER'
            self.recover_until = None
        if path is None or len(path) < 3:
            self.speed = 0.
            self.blocked_since = self.blocked_since or now
            if now-self.blocked_since > 1.:
                self.blocked_since = None
                distance, self.recover_steer = self._choose_reverse(pose)
                self.recover_until = now+distance/cfg.recover_speed
            return 0., self.sign*self.steer, 'PLAN_BLOCKED'
        self.blocked_since = None
        # Pure pursuit on the planned path, from the pose predicted after the
        # steering latency (measured yaw rate; the servo lags ~0.35-0.5 s in sim).
        d = np.hypot(path[:, 0]-x, path[:, 1]-y)
        i0 = int(np.argmin(d))
        ahead = path[i0:]
        lookahead = cfg.plan_lookahead+.25*max(self.speed, 0.)
        far = np.nonzero(np.hypot(ahead[:, 0]-x, ahead[:, 1]-y) >= lookahead)[0]
        target = ahead[far[0]] if far.size else ahead[-1]
        alpha = wrap(math.atan2(target[1]-y, target[0]-x)-th)
        ld = max(math.hypot(target[0]-x, target[1]-y), .05)
        steer = math.atan2(2*WHEELBASE*math.sin(alpha), ld)
        if cfg.plan_latency > 0.:
            # Feedforward: the planned steering where the car will be after the
            # servo latency, plus pure-pursuit feedback around the current plan.
            k = min(len(ahead)-1, int(round(max(self.speed, 0.)*cfg.plan_latency/cfg.plan_ds)))
            steer = ahead[k, 3]+cfg.plan_feedback*(steer-ahead[0, 3])
        steer = max(-cfg.steer_limit, min(cfg.steer_limit, steer))
        # Speed: curvature ahead, braking to the end of the path and to the goal.
        kappa = np.max(np.abs(np.tan(ahead[:12, 3])))/WHEELBASE
        v = min(cfg.plan_speed, math.sqrt(cfg.plan_lat_accel/max(kappa, 1e-3)))
        length = cfg.plan_ds*(len(ahead)-1)
        v = min(v, math.sqrt(max(0., 2*cfg.plan_brake*(length-.12))))
        v = min(v, math.sqrt(max(0., 2*cfg.plan_brake*remaining*1.)))
        if remaining < .3:
            v = min(v, cfg.finish_speed)
        v = max(v, 0.)
        self.speed, self.steer = v, steer
        return v, self.sign*steer, self.state

    def _choose_reverse(self, pose):
        """Try short reverse arcs; keep the one whose forward plan progresses most.

        An unknown-colour pillar nearby adds credit for facing it (camera +-30 deg).
        """
        cfg = self.cfg
        pillars = self.map.pillars()
        unknown = [p for p in pillars if p['color'] is None]
        best = (-math.inf, cfg.plan_recover_distance, 0.)
        bad0 = self.planner.wrong_side(*pose, pillars)
        for distance in (.15, .3, .45):
            for steer in (-cfg.steer_limit, -cfg.steer_limit/2, 0., cfg.steer_limit/2, cfg.steer_limit):
                x, y, th = pose
                ok = True
                for _ in range(6):
                    step = -distance/6
                    th2 = th+step*math.tan(steer)/WHEELBASE
                    x += step*math.cos((th+th2)/2); y += step*math.sin((th+th2)/2); th = th2
                    if not self.planner.pose_ok(x, y, th, pillars, .005) or \
                            self.planner.wrong_side(x, y, th, pillars)-bad0:
                        ok = False
                        break
                if not ok:
                    continue
                phi = float(unwrap_s(self.phi, track_s(x, y)))
                path = self.planner.plan((x, y, th), steer, pillars, phi, self.phi_goal)
                score = self.planner.last_progress if path is not None and len(path) >= 3 else phi-1.
                for p in unknown:
                    bearing = wrap(math.atan2(p['y']-y, p['x']-x)-th)
                    if abs(bearing) < .4 and math.hypot(p['x']-x, p['y']-y) < 1.5:
                        score += .5
                score -= .2*distance
                if score > best[0]:
                    best = (score, distance, steer)
        return best[1], best[2]

    def _reverse_clear(self, pose, back=.06):
        x, y, th = pose
        c, s = math.cos(th), math.sin(th)
        pillars = self.map.pillars()
        bx, by = x-c*back, y-s*back
        if not self.planner.pose_ok(bx, by, th, pillars, .005) or \
                self.planner.wrong_side(bx, by, th, pillars)-self.planner.wrong_side(x, y, th, pillars):
            return False
        for u, v in ((-REAR_L-back, HALF_W), (-REAR_L-back, -HALF_W)):
            px, py = x+c*u-s*v, y+s*u+c*v
            m = max(abs(px), abs(py))
            if m > OUTER-.005 or m < INNER+.005:
                return False
        return True

    def snapshot(self):
        return dict(pose=self.pose(), phi=self.phi, phi_goal=self.phi_goal, state=self.state,
                    inliers=self.loc.inliers, rms=self.loc.rms, plan_ms=self.plan_ms,
                    path_len=None if self.path is None else len(self.path),
                    pillars=[(p['id'], p['color']) for p in self.map.pillars()])
