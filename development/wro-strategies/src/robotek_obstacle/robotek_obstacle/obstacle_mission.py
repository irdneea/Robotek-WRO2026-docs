"""Obstacle round: CALIBRATE -> DETECT_DIRECTION -> driver (PLAN ... DONE).

- CALIBRATE: stand still and average the gyro (its bias).
- DETECT_DIRECTION: fit the known walls for CCW and CW on each new scan; a clear
  winner picks the direction. Between scans the camera lines may decide instead,
  while creeping straight on the gyro heading (fallback; the lidar usually wins
  on the first scan).
- Then ObstacleDriver plans and drives the three laps and stops (PLAN ... DONE).
"""
import math

import numpy as np

from .obstacle_driver import ObstacleDriver
from .obstacle_field import wrap
from .obstacle_localizer import direction_from_scan
from .obstacle_parking import ObstacleParking
from .obstacle_perception import LineDirection

SIDE_CENTER = 1.5708    # rad, side lidar windows at +-90 deg
SIDE_HALF_WIDTH = .44
FRONT_HALF_WIDTH = .35  # rad, front lidar window
INNER_OPEN = 1.0        # m; a side this open while the other is near (<0.9 m) is the island side
PROBE_FRONT = .65       # m free ahead to creep while reading the lines


def _window(scan, center, half):
    """Valid ranges within +-half of a bearing."""
    r = np.asarray(scan.ranges, dtype=float)
    if r.size == 0:
        return np.empty(0)
    ang = scan.angle_min+np.arange(r.size)*scan.angle_increment
    rel = np.arctan2(np.sin(ang-center), np.cos(ang-center))
    valid = np.isfinite(r) & (r >= max(.16, scan.range_min)) & (r <= scan.range_max)
    return r[(np.abs(rel) <= half) & valid]


class ObstacleMission:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lines = LineDirection(cfg.vision_min_length, cfg.vision_min_confidence,
                                   cfg.vision_confirmations)
        self.state = 'WAIT_START'
        self.driver = None
        self.parking = None
        self.selected_direction = ''
        self.direction_reason = ''
        self.direction_margin = math.nan
        self.gyro_bias = 0.
        self.yaw_zero = 0.
        self._last_now = None
        self._calib = [0., 0., 0]  # elapsed s, gyro sum, samples
        self._detect_t = 0.
        self._wall_scan = self._direction_scan = -math.inf
        self._hint = 0
        self._front = math.inf

    def image(self, bgr, stamp):
        self.lines.update(bgr, stamp)

    def observe(self, observations):
        if self.driver:
            self.driver.on_observations(observations)

    def step(self, now, scan, scan_stamp, image_stamp, yaw, gyro, distance):
        """One control cycle -> (speed, steer, state). distance: travelled since the last cycle."""
        dt = 0. if self._last_now is None else max(0., min(.1, now-self._last_now))
        self._last_now = now
        gyro -= self.gyro_bias
        if scan_stamp > self._wall_scan:
            self._read_walls(scan)
            self._wall_scan = scan_stamp
        if self.state == 'DETECT_DIRECTION' and scan is not None and scan_stamp > self._direction_scan:
            self._direction_scan = scan_stamp
            sign, self.direction_margin = direction_from_scan(scan)
            if self.direction_margin >= self.cfg.plan_direction_margin:
                self._select(sign, 'lidar_wall_fit')
        if self.state == 'DIRECTION_SET':
            return self._drive(now, scan, scan_stamp, yaw, distance)
        if self.state == 'WAIT_START':
            self.state = 'CALIBRATE'
        elif self.state == 'CALIBRATE':
            self._step_calibrate(dt, yaw, gyro)
        elif self.state == 'DETECT_DIRECTION':
            return self._step_detect(dt, now-image_stamp, yaw, gyro)
        return 0., 0., self.state

    # ------------------------------------------------------------- states
    def _step_calibrate(self, dt, yaw, gyro):
        c = self._calib
        c[0] += dt
        c[1] += gyro
        c[2] += 1
        if c[0] >= self.cfg.calibrate_seconds:
            self.gyro_bias = c[1]/c[2]
            self.yaw_zero = yaw
            self.state = 'DETECT_DIRECTION'

    def _step_detect(self, dt, image_age, yaw, gyro):
        cfg = self.cfg
        self._detect_t += dt
        visual = self.lines.direction if image_age <= .5 else 0
        hint = self._hint
        if visual and (not hint or hint == visual):
            self._select(visual, 'camera_and_lidar' if hint else 'camera_confirmed')
            return 0., 0., 'DIRECTION_SET'
        if self._detect_t >= cfg.direction_timeout:
            self.direction_reason = 'ambiguous_or_conflicting_evidence'
            self.state = 'DIRECTION_FAULT'
            return 0., 0., self.state
        # Do not creep into a nearby wall or while camera and lidar disagree.
        if (visual and hint and visual != hint) or image_age > .5 or self._front < PROBE_FRONT:
            return 0., 0., self.state
        error = wrap(-wrap(yaw-self.yaw_zero))
        steer = cfg.heading_kp*error-cfg.heading_kd*gyro
        return cfg.direction_probe_speed, max(-cfg.steer_limit, min(cfg.steer_limit, steer)), self.state

    def _drive(self, now, scan, scan_stamp, yaw, distance):
        if self.driver is None:
            sign = 1. if self.selected_direction == 'ccw' else -1.
            self.driver = ObstacleDriver(self.cfg, sign, yaw)
        new_scan = scan_stamp > self._direction_scan
        if new_scan:
            self.driver.on_scan(scan)
            self._direction_scan = scan_stamp
        if self.cfg.mode == 'park':
            if self.parking is None:
                self.parking = ObstacleParking(self.cfg, self.driver)
            return self.parking.step(now, yaw, distance, scan if new_scan else None)
        return self.driver.step(now, yaw, distance)

    # ------------------------------------------------------------ helpers
    def _select(self, sign, reason):
        self.selected_direction = 'ccw' if sign > 0 else 'cw'
        self.direction_reason = reason
        self.state = 'DIRECTION_SET'

    def _read_walls(self, scan):
        """Island side from the side walls (hint) and free space ahead."""
        left, right = _window(scan, SIDE_CENTER, SIDE_HALF_WIDTH), _window(scan, -SIDE_CENTER, SIDE_HALF_WIDTH)
        left = float(np.median(left)) if left.size else math.inf
        right = float(np.median(right)) if right.size else math.inf
        self._hint = 0
        if math.isfinite(left) and math.isfinite(right):
            if left > INNER_OPEN and right < .9:
                self._hint = 1
            elif right > INNER_OPEN and left < .9:
                self._hint = -1
        front = _window(scan, 0., FRONT_HALF_WIDTH)
        self._front = float(np.min(front)) if front.size else math.inf
