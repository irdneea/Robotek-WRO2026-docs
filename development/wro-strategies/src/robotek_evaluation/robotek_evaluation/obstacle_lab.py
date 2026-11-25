"""Obstacle lab: one Obstacle round in a few seconds, without Gazebo.

A closed-loop simulator for iterating on Obstacle strategies fast, built from the same
pieces the Gazebo runs use so its results can be checked against them:

* the regulation field and the signs of a recorded round (its ``world.sdf`` and
  ``manifest.json``): walls and pillars are boxes, ray casing for the LiDAR;
* the real-car actuators (``open_lab.Actuators``: servo delay/rate/lag and the motor
  speed table of ``real_car_v1.yaml``);
* the LD19 scan (10 Hz, 306 rays over +-110 deg, 8 mm noise, 4.3 % dropouts, each stamp
  delivered three times), a 50 Hz gyroscope with bias and noise, and a 6 fps camera that
  reports the bearing and colour of the pillars in view (the real car's 66.7 deg field of view,
  turned 4.4 deg left, as Gazebo with ``real_car:=true``), hidden by walls, signs and lot limits
  in 3D (camera 14.2 cm high) and kept only if the visible part passes ``color_blocks``' filter;
* the current Obstacle strategy (``ObstacleMission``) wired like its node: LiDAR odometry
  for distance, integrated gyro for heading, camera observations for the colours;
* the Gazebo judge (``obstacle_full_round_report.summarize_full``) applied to the lab
  trajectory, so points, faults and validity mean the same thing.

What it does NOT model: wheel slip, the Ackermann plugin, images (colours are given
directly; the occlusion test samples the sign's face), contact forces (a contact ends the round) or pillar movement (a
pillar is static; touching it is a contact). It is a one-way filter: failing here is bad
news, passing here proves nothing until Gazebo agrees (``--compare``).

    python3 -m robotek_evaluation.obstacle_lab --run docs/obstacle-challenge-runs/<round>
"""
import argparse
import csv
import json
import math
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from robotek_common import vehicle
from robotek_common.lidar_odometry import LidarOdometry
from robotek_common.vehicle import DISTANCE_MODEL_ACCEL
from .obstacle_full_round_report import summarize_full
from .open_lab import CARS, Actuators, actuator_parameters, car_profile, full_circle, outline

def _repo_root():
    """Repository root: the working directory when it holds docs/, else a source checkout."""
    cwd = Path.cwd()
    if (cwd / 'docs' / 'obstacle-challenge-runs').exists():
        return cwd
    for parent in Path(__file__).resolve().parents:
        if (parent / 'docs' / 'obstacle-challenge-runs').exists():
            return parent
    return cwd


def _share(package, fallback):
    try:
        from ament_index_python.packages import get_package_share_directory
        return Path(get_package_share_directory(package))
    except Exception:
        return fallback


ROOT = _repo_root()
RUNS = ROOT / 'docs' / 'obstacle-challenge-runs'
DEFAULT_RUN = RUNS / '20261022-090215-obs-base-a-reg0-ccw'
PROFILE = _share('robotek_obstacle', ROOT / 'src' / 'robotek_obstacle') / 'config' / 'obstacle_sensors_v1.yaml'
ACTUATOR_CONFIG = _share('robotek_evaluation', ROOT / 'src' / 'robotek_evaluation') / 'config' / 'real_car_v1.yaml'

PHYSICS_HZ = 100.0
CONTROL_EVERY = 2            # 50 Hz, as the node
SCAN_EVERY = 10              # 10 Hz LiDAR
IMU_EVERY = 2                # 50 Hz gyroscope
CAMERA_PERIOD = 1.0 / 6.0    # 6 fps camera
TELEMETRY_EVERY = 10         # 10 Hz rows for the judge
SCAN_RAYS = 306
SCAN_HALF_ANGLE = math.radians(110.0)
SCAN_MIN_RANGE = 0.12
SCAN_NOISE = 0.008
SCAN_DROPOUT = 0.043
SCAN_COPIES = 3
SCAN_MAX_RANGE = 4.0
GYRO_NOISE = 0.0019
GYRO_BIAS = 0.006
CAMERA_RANGE = 2.0           # m; colours are only reported this far
CAMERA_BEARING_NOISE = 0.01  # rad
CAMERA_FOCAL = 320.0 / math.tan(vehicle.REAL_CAMERA_HFOV / 2)  # px, 640-px wide image
FACE_COLUMNS, FACE_ROWS = 5, 8   # samples on a sign's face for the camera's occlusion test
MIN_BLOB_AREA, MIN_BLOB_HEIGHT, BLOB_ASPECT = 30.0, 8.0, 1.05   # px; the filter of color_blocks
STOP_HOLD = 31.0
CONTROL_PERIOD = CONTROL_EVERY / PHYSICS_HZ


# ------------------------------------------------------------------- world
class World:
    """Regulation field and sign boxes of a recorded round."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.manifest = json.loads((self.directory / 'manifest.json').read_text())
        self.pillars = self.manifest['pillars']
        root = ET.parse(self.directory / 'world.sdf').getroot()
        boxes, kinds, tops = [], [], []
        for node in root.findall(".//model[@name='game_field']//collision"):
            name = node.get('name', '')
            if not name.startswith('wall_'):
                continue
            boxes.append(self._box(node))
            kinds.append('inner_wall' if name.startswith('wall_int') else 'outer_wall')
            z = float(node.findtext('pose', '0 0 0').split()[2])
            height = float(node.findtext('geometry/box/size').split()[2])
            tops.append(z + height / 2)
        # Parking lot limits (rounds with the lot): static boxes that stop the round when touched.
        for link in root.findall(".//model[@name='parking_lot']/link"):
            x, y, z = [float(v) for v in link.findtext('pose').split()[:3]]
            sx, sy, sz = [float(v) for v in link.find('collision/geometry/box/size').text.split()[:3]]
            boxes.append((x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2))
            kinds.append('parking_limit')
            tops.append(z + sz / 2)
        self.lot = self.manifest.get('parking_lot')
        self.wall_boxes = np.array(boxes, dtype=float)
        self.kinds = kinds
        # Pillars: the manifest is what the round was built from; the SDF link pose is not
        # the collision's world pose (the collision pose is local to the link).
        self.sign_boxes = np.array([(p['x'] - p['size_m'][0] / 2, p['x'] + p['size_m'][0] / 2,
                                     p['y'] - p['size_m'][1] / 2, p['y'] + p['size_m'][1] / 2)
                                    for p in self.pillars], dtype=float).reshape(-1, 4)
        # Every box that can hide a sign from the camera, with its top (signs stand on the floor).
        self.view_boxes = np.vstack([self.wall_boxes.reshape(-1, 4), self.sign_boxes])
        self.view_tops = np.array(tops + [p['size_m'][2] for p in self.pillars], dtype=float)
        self.path = self.directory

    @staticmethod
    def _box(node):
        pose = [float(v) for v in node.findtext('pose', '0 0 0 0 0 0').split()]
        size = [float(v) for v in node.findtext('geometry/box/size').split()]
        return (pose[0] - size[0] / 2, pose[0] + size[0] / 2,
                pose[1] - size[1] / 2, pose[1] + size[1] / 2)

    def raycast(self, ox, oy, angles):
        """Distance from (ox, oy) along each angle to the nearest wall or sign box."""
        best = np.full(angles.shape, np.inf)
        for boxes in (self.wall_boxes, self.sign_boxes):
            if not len(boxes):
                continue
            for xmin, xmax, ymin, ymax in boxes:
                best = np.minimum(best, _ray_box(ox, oy, angles, xmin, xmax, ymin, ymax))
        return best

    def clearances(self, polygon):
        """Smallest distance from the car outline to each kind of obstacle (<= 0 touches)."""
        from .open_lab import _inside, _perimeter
        out = {'outer_wall': math.inf, 'inner_wall': math.inf, 'pillar': math.inf}
        if self.lot:
            out['parking_limit'] = math.inf
        samples = _perimeter(polygon, 0.02)
        for (xmin, xmax, ymin, ymax), kind in zip(self.wall_boxes, self.kinds):
            distance = _box_distance(samples, polygon, xmin, xmax, ymin, ymax)
            out[kind] = min(out[kind], distance)
        for xmin, xmax, ymin, ymax in self.sign_boxes:
            out['pillar'] = min(out['pillar'], _box_distance(samples, polygon, xmin, xmax, ymin, ymax))
        return out


def _ray_box(ox, oy, angles, xmin, xmax, ymin, ymax):
    dx, dy = np.cos(angles), np.sin(angles)
    with np.errstate(divide='ignore', invalid='ignore'):
        tx = np.stack([(xmin - ox) / dx, (xmax - ox) / dx])
        ty = np.stack([(ymin - oy) / dy, (ymax - oy) / dy])
        near = np.maximum(tx.min(axis=0), ty.min(axis=0))
        far = np.minimum(tx.max(axis=0), ty.max(axis=0))
        hit = (far >= near) & (near > 1e-6)
    return np.where(hit, near, np.inf)


def _box_distance(samples, polygon, xmin, xmax, ymin, ymax):
    from .open_lab import _inside
    dx = np.maximum(np.maximum(xmin - samples[:, 0], samples[:, 0] - xmax), 0.0)
    dy = np.maximum(np.maximum(ymin - samples[:, 1], samples[:, 1] - ymax), 0.0)
    distance = float(np.hypot(dx, dy).min())
    corners = np.array([(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)])
    if _inside(polygon, corners).any():
        distance = 0.0
    return distance


class SideWatch:
    """Cheap early warning of a wrong-side pass: the car's centre crosses a sign's radius
    line on the side the colour forbids. Only clear faults count (the centre itself is on
    the wrong side), so it never ends a round the judge would accept."""

    TANGENTS = {'bottom': (1, 0), 'right': (0, 1), 'top': (-1, 0), 'left': (0, -1)}

    def __init__(self, pillars, direction):
        sign = 1 if direction == 'ccw' else -1
        self.signs = []
        for p in pillars:
            tx, ty = self.TANGENTS[p['side']]
            self.signs.append((p, tx * sign, ty * sign))
        self.before = {p['name']: False for p in pillars}

    def wrong(self, x, y):
        for p, tx, ty in self.signs:
            horizontal = p['side'] in ('bottom', 'top')
            near = (abs(x - p['x']) < .6 and y * math.copysign(1, p['y']) >= .45) if horizontal else \
                (abs(y - p['y']) < .6 and x * math.copysign(1, p['x']) >= .45)
            if not near:
                continue
            along = tx * (x - p['x']) + ty * (y - p['y'])
            if along < 0:
                self.before[p['name']] = True
            elif self.before[p['name']]:
                self.before[p['name']] = False
                lateral = -ty * (x - p['x']) + tx * (y - p['y'])
                if (lateral > 0) == (p['color'] == 'red'):
                    return True
        return False


FAULT_GRACE = 1.5            # s simulated after a clear wrong-side pass (the judge needs the car past)


# ---------------------------------------------------------------- strategy
class CurrentStrategy:
    """ObstacleMission wired like ``ObstacleStrategyNode``: LiDAR odometry, integrated gyro,
    camera observations. Inputs in the car frame, outputs (speed, steer)."""

    def __init__(self, overrides=None):
        from dataclasses import fields
        from robotek_obstacle.obstacle_config import ObstacleConfig, config_with
        from robotek_obstacle.obstacle_mission import ObstacleMission
        params = {}
        if PROFILE.exists():
            params = yaml.safe_load(PROFILE.read_text())['obstacle_strategy']['ros__parameters'] or {}
        known = {f.name for f in fields(ObstacleConfig)}
        params = {k: v for k, v in {**params, **(overrides or {})}.items() if k in known}
        self.mission = ObstacleMission(config_with(**params))
        self.odometry = LidarOdometry(accel=DISTANCE_MODEL_ACCEL)
        self.yaw = 0.0
        self.gyro = 0.0
        self._imu_time = None
        self._last_speed = 0.0
        self.travelled = 0.0
        self.scan = None
        self.scan_stamp = -math.inf
        self.image_stamp = -math.inf
        self.state = 'WAIT_START'
        self.started = None
        self.done_at = None

    def on_scan(self, scan, now):
        self.scan, self.scan_stamp = scan, now
        self.odometry.scan(scan, self.yaw)

    def on_imu(self, now, gyro_z):
        if self._imu_time is not None and 0.0 < now - self._imu_time < 0.2:
            self.yaw += (gyro_z - self.mission.gyro_bias) * (now - self._imu_time)
        self._imu_time = now
        self.gyro = gyro_z

    def on_camera(self, observations, now):
        self.image_stamp = now
        self.mission.observe(observations)

    def distance_step(self):
        """Distance since the last cycle; ignored while stopped, as the node does."""
        self.odometry.command(self._last_speed, CONTROL_PERIOD)
        step = self.odometry.read()
        if self.mission.driver is None or (abs(self._last_speed) < .01 and abs(self.odometry.speed_model) < .01):
            return 0.0
        self.travelled += step
        return step

    def control(self, now):
        distance = self.distance_step()
        self.travelled += distance
        speed, steer, state = self.mission.step(
            now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, distance)
        self._last_speed = speed
        self.state = state
        if state in ('DONE', 'PARKED') and self.done_at is None:
            self.done_at = now
        return speed, steer

    @property
    def label(self):
        return self.state

    @property
    def done(self):
        return self.done_at is not None


class V2Strategy:
    """The v2 mission wired like its node: LiDAR odometry, integrated gyro, camera observations."""

    def __init__(self, overrides=None, version='v2'):
        from importlib import import_module
        self.mission = import_module(f'robotek_obstacle.{version}.mission').Mission(overrides)
        self.odometry = LidarOdometry(accel=DISTANCE_MODEL_ACCEL)
        self.yaw = 0.0
        self.gyro = 0.0
        self._imu_time = None
        self._last_speed = 0.0
        self.scan = None
        self.scan_stamp = -math.inf
        self.image_stamp = -math.inf
        self.started = None
        self.done_at = None
        self.travelled = 0.0

    def on_scan(self, scan, now):
        # Gazebo delivers each scan stamp several times; the v2 aligns each stamp once
        # (a repeated copy only adds alignment noise to the distance).
        if now > self.scan_stamp:
            self.odometry.scan(scan, self.yaw)
        self.scan, self.scan_stamp = scan, now

    def on_imu(self, now, gyro_z):
        if self._imu_time is not None and 0.0 < now - self._imu_time < 0.2:
            self.yaw += (gyro_z - self.mission.gyro_bias) * (now - self._imu_time)
        self._imu_time = now
        self.gyro = gyro_z

    def on_camera(self, observations, now):
        self.image_stamp = now
        self.mission.observe(observations, now)

    def control(self, now):
        self.odometry.command(self._last_speed, CONTROL_PERIOD)
        step = self.odometry.read()
        distance = 0.0 if (self.mission.loc.ready is False or
                           (abs(self._last_speed) < .01 and abs(self.odometry.speed_model) < .01)) else step
        self.travelled += distance
        speed, steer, state = self.mission.step(
            now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, distance)
        self._last_speed = speed
        if state == 'STOP' and self.done_at is None:
            self.done_at = now
        return speed, steer

    @property
    def label(self):
        return self.mission.state

    @property
    def done(self):
        return self.done_at is not None


def strategy_factory(name, overrides=None):
    if name in ('v2', 'v3'):
        return lambda: V2Strategy(overrides, name)
    return lambda: CurrentStrategy(overrides)


def make_scan(ranges, now, angle_min, increment):
    from types import SimpleNamespace
    sec = int(now)
    return SimpleNamespace(
        ranges=ranges, angle_min=angle_min, angle_increment=increment,
        range_min=SCAN_MIN_RANGE, range_max=SCAN_MAX_RANGE,
        header=SimpleNamespace(stamp=SimpleNamespace(sec=sec, nanosec=int(round((now - sec) * 1e9)))))


def _seen(world, cx, cy, index):
    """Whether the camera at (cx, cy) sees enough of sign ``index`` for ``color_blocks``.

    The sign's face (across the line of sight) is sampled; a sample is hidden when its 3D ray
    crosses another box (wall, sign or lot limit) below that box's top. The camera is above the
    10 cm signs and 11 cm walls, so a far sign may still show its top over a near one. The visible
    part must pass the filter of ``color_blocks``: at least MIN_BLOB_AREA px, MIN_BLOB_HEIGHT px
    tall and BLOB_ASPECT times taller than wide (a sign showing only its top is rejected).
    """
    pillar = world.pillars[index]
    width, _, height = pillar['size_m']
    dx, dy = pillar['x'] - cx, pillar['y'] - cy
    distance = math.hypot(dx, dy)
    across = np.linspace(-width / 2, width / 2, FACE_COLUMNS)
    sx, sy = pillar['x'] - across * dy / distance, pillar['y'] + across * dx / distance
    angles, reach = np.arctan2(sy - cy, sx - cx), np.hypot(sx - cx, sy - cy)          # (C,)
    boxes = np.delete(world.view_boxes, len(world.wall_boxes) + index, axis=0)
    tops = np.delete(world.view_tops, len(world.wall_boxes) + index)
    ux, uy = np.cos(angles)[None, :], np.sin(angles)[None, :]
    with np.errstate(divide='ignore', invalid='ignore'):
        tx = np.stack([(boxes[:, 0, None] - cx) / ux, (boxes[:, 1, None] - cx) / ux])
        ty = np.stack([(boxes[:, 2, None] - cy) / uy, (boxes[:, 3, None] - cy) / uy])
        near = np.maximum(np.nanmin(tx, axis=0), np.nanmin(ty, axis=0))                # (B, C)
        far = np.minimum(np.nanmax(tx, axis=0), np.nanmax(ty, axis=0))
    crossed = (far >= np.maximum(near, 0.0)) & (near < reach)
    # The ray goes down from the camera to the sample, so it is lowest where it leaves the box.
    leave = np.minimum(far, reach)
    rows = (np.arange(FACE_ROWS) + 0.5) * height / FACE_ROWS                           # (R,)
    ray_z = (vehicle.REAL_CAMERA_HEIGHT
             + (rows[None, None, :] - vehicle.REAL_CAMERA_HEIGHT) * (leave / reach)[:, :, None])
    hidden = (crossed[:, :, None] & (ray_z < tops[:, None, None])).any(axis=0)       # (C, R)
    visible = ~hidden
    if not visible.any():
        return False
    columns = np.flatnonzero(visible.any(axis=1))
    levels = np.flatnonzero(visible.any(axis=0))
    scale = CAMERA_FOCAL / distance                                                    # px per m
    blob_w = (columns[-1] - columns[0] + 1) / FACE_COLUMNS * width * scale
    blob_h = (levels[-1] - levels[0] + 1) / FACE_ROWS * height * scale
    area = visible.mean() * width * height * scale ** 2
    return area >= MIN_BLOB_AREA and blob_h >= MIN_BLOB_HEIGHT and blob_h >= BLOB_ASPECT * blob_w


def camera_observations(world, x, y, yaw, rng, max_range=CAMERA_RANGE, occlusion=True):
    """Pillars in the camera's field of view, as ``associate`` would report them; with
    ``occlusion`` only the ones the camera sees over and around the other boxes (``_seen``)."""
    from robotek_obstacle.obstacle_field import CAMERA_OFFSET_X
    observations = []
    c, s = math.cos(yaw), math.sin(yaw)
    cx, cy = x + vehicle.CAMERA_OFFSET_X * c, y + vehicle.CAMERA_OFFSET_X * s
    for index, pillar in enumerate(world.pillars):
        dx, dy = pillar['x'] - x, pillar['y'] - y
        bx, by = c * dx + s * dy, -s * dx + c * dy
        range_m = math.hypot(bx - CAMERA_OFFSET_X, by)
        if not SCAN_MIN_RANGE < range_m < max_range:
            continue
        bearing = math.atan2(by, bx - CAMERA_OFFSET_X)
        # The real car's camera (and Gazebo with real_car:=true): 66.7 deg, turned 4.4 deg left.
        if abs(bearing - vehicle.REAL_CAMERA_YAW) > vehicle.REAL_CAMERA_HFOV / 2:
            continue
        if occlusion and not _seen(world, cx, cy, index):
            continue
        observations.append(dict(x=bx + rng.normal(0.0, 0.01), y=by + rng.normal(0.0, 0.01),
                                 color=pillar['color']))
    return observations


# ------------------------------------------------------------------- round
def run_round(directory, direction=None, spawn=None, seed=0, tmax=180.0, overrides=None,
              camera_range=CAMERA_RANGE, trace=False, strategy_name='current', stop_on_fault=False,
              occlusion=True, car=None):
    """One lab round on the field of a recorded round. Returns the result dict.

    ``stop_on_fault`` ends the round shortly after the car's centre passes a sign on the
    wrong side (the judge would end the scoring there anyway); the judge still decides.
    ``car``: an ``open_lab.car_profile`` (None: the Gazebo car real_car_v1, as before). With real_v2 the
    actuators are the real car of 4 nov 2026 (measured steering and motor curve), each scan comes once and the
    node's 50 Hz control timer ticks at the rate measured on the Pi (control_hz). The v3 integrates the gyro with
    the IMU stamps, so a slow timer does not bend its yaw (unlike the Open v5 before 9ce7d67).
    """
    world = World(directory)
    sides = SideWatch(world.pillars, direction or world.manifest['direction']) if stop_on_fault else None
    fault_at = None
    direction = direction or world.manifest['direction']
    spawn = spawn or _spawn(world.manifest, direction)
    strategy = strategy_factory(strategy_name, overrides)()
    actuators = Actuators(car['actuator'] if car else actuator_parameters(ACTUATOR_CONFIG))
    scan_copies = car['scan_copies'] if car else SCAN_COPIES
    control_hz = car.get('control_hz') if car else None
    # real_v4 (11 nov 2026): the car's LD19 layout (504 rays, 0..2 pi), whole scans lost and a gyro that reads short.
    # Off with the other profiles (their numbers are unchanged).
    scan_full_circle = bool(car.get('scan_full_circle')) if car else False
    gap_rate = car.get('scan_gap_rate', 0.0) if car else 0.0
    gap_max = car.get('scan_gap_max', 0.0) if car else 0.0
    gyro_scale = car.get('gyro_scale', 1.0) if car else 1.0
    gap_until = -math.inf
    last_slot = None
    # The real car's brake resets the board, which also stops its IMU for brake_imu_gap s (real_v2).
    imu_gap = actuators.p.get('brake_imu_gap', 0.0) if actuators.p.get('brake_decel', 0.0) > 0.0 else 0.0
    braked_at, imu_back, resets = None, -math.inf, 0
    rng = np.random.default_rng(seed)
    sign = 1.0 if direction == 'ccw' else -1.0
    yaw = 0.0 if direction == 'ccw' else math.pi
    back = -vehicle.REAR_AXLE_X
    xr, yr = spawn[0] - back * math.cos(yaw), spawn[1] - back * math.sin(yaw)
    x, y = spawn
    angle_min = -SCAN_HALF_ANGLE
    increment = -2.0 * angle_min / (SCAN_RAYS - 1)
    beams = angle_min + increment * np.arange(SCAN_RAYS)
    bias = GYRO_BIAS + rng.normal(0.0, 0.0005)
    dt = 1.0 / PHYSICS_HZ
    rows, events = [], []
    t_start = None
    camera_time = None
    contact = None
    contact_info = None
    clearance = {'outer_wall': math.inf, 'inner_wall': math.inf, 'pillar': math.inf}
    if world.lot:
        clearance['parking_limit'] = math.inf
    steer_max = 0.0
    yaw_rate = 0.0
    stopped_at = None
    last_speed = 0.0
    for tick in range(int(tmax / dt)):
        now = tick * dt
        if tick % SCAN_EVERY == 0 and gap_rate > 0.0 and now >= gap_until and \
                rng.random() < gap_rate * SCAN_EVERY * dt:
            gap_until = now + rng.uniform(0.2, max(0.2, gap_max))   # the LD19 skips whole scans (11 nov 2026)
        if tick % SCAN_EVERY == 0 and now >= gap_until:
            ranges = world.raycast(x + vehicle.LIDAR_OFFSET_X * math.cos(yaw),
                                   y + vehicle.LIDAR_OFFSET_X * math.sin(yaw), beams + yaw)
            ranges = ranges + rng.normal(0.0, SCAN_NOISE, SCAN_RAYS)
            ranges[(ranges < SCAN_MIN_RANGE) | ~np.isfinite(ranges)] = math.inf
            for copy in range(scan_copies):
                scan_ranges = ranges.copy()
                scan_ranges[rng.random(SCAN_RAYS) < SCAN_DROPOUT] = math.inf
                message = full_circle(list(scan_ranges), angle_min, increment) if scan_full_circle \
                    else (list(scan_ranges), angle_min, increment)
                strategy.on_scan(make_scan(message[0], now, *message[1:]), now)
        if imu_gap and actuators.zero_since is not None and actuators.zero_since != braked_at \
                and abs(actuators.v_out) > 1e-3:
            braked_at = actuators.zero_since           # a stop after moving: the board is reset
            imu_back = braked_at + actuators.p.get('brake_delay', 0.0) + imu_gap
            resets += 1
        if tick % IMU_EVERY == 0 and now >= imu_back:
            strategy.on_imu(now, gyro_scale * yaw_rate + bias + rng.normal(0.0, GYRO_NOISE))
        if control_hz:                       # the Pi's timer: control_hz ticks a second instead of 50
            slot = int(now * control_hz + 1e-9)
            control_due, last_slot = slot != last_slot, slot
        else:
            control_due = tick % CONTROL_EVERY == 0
        if control_due:
            if camera_time is None or now - camera_time >= CAMERA_PERIOD - 1e-9:
                camera_time = now
                # The node only associates colours with a LiDAR cluster from a scan no older
                # than 0.15 s, and the camera sees a 50 mm sign only up close.
                if strategy.scan is not None and now - strategy.scan_stamp <= 0.15:
                    strategy.on_camera(camera_observations(world, x, y, yaw, rng, camera_range,
                                                                  occlusion), now)
            speed, steer = strategy.control(now)
            actuators.command(now, speed, steer)
            last_speed = speed
            if t_start is None and strategy.started is None:
                t_start = now
                strategy.started = now
                events.append({'event': 'start', 'sim_time': now, 'wall_time': now})
        v_out, commanded_rate = actuators.step(now, dt)
        yaw_rate = commanded_rate
        yaw += yaw_rate * dt
        xr += v_out * math.cos(yaw) * dt
        yr += v_out * math.sin(yaw) * dt
        x, y = xr + back * math.cos(yaw), yr + back * math.sin(yaw)
        steer_max = max(steer_max, abs(actuators.steer))
        if tick % CONTROL_EVERY == 0:
            current = world.clearances(outline(x, y, yaw))
            clearance = {k: min(clearance[k], current[k]) for k in clearance}
            worst = min(clearance.values())
            if contact is None and worst <= 0.0:
                contact = now
                contact_info = _contact(world, current, x, y, now)
        if tick % TELEMETRY_EVERY == 0:
            rows.append(_row(now, strategy.label, x, y, yaw, actuators.steer, direction))
        if contact is not None or now - t_start > tmax:
            break
        if sides is not None and tick % TELEMETRY_EVERY == 0:
            if fault_at is None and sides.wrong(x, y):
                fault_at = now
            if fault_at is not None and now - fault_at > FAULT_GRACE:
                break
        if strategy.done and stopped_at is None:
            stopped_at = now
            events.append({'event': 'done', 'sim_time': now, 'wall_time': now})
        if stopped_at is not None and abs(v_out) < 1e-3 and now - stopped_at > 1.0:
            break
    if stopped_at is not None and contact is None and rows:
        last = rows[-1]
        count = int(STOP_HOLD * PHYSICS_HZ / TELEMETRY_EVERY)
        rows.extend(_row(last['sim_time'] + (i + 1) * TELEMETRY_EVERY / PHYSICS_HZ, last['state'],
                         x, y, yaw, actuators.steer, direction) for i in range(count))
    result = _judge(world, direction, rows, events, contact_info, clearance, steer_max, trace)
    result.update(car=car['name'] if car else 'gazebo', board_resets=resets)
    result.update(run=str(directory), direction=direction, contact_time=contact,
                  contact=contact_info, end=strategy.label, travels=strategy.travelled)
    return result


def _spawn(manifest, direction):
    """Start pose: the runner spawns at (spawn_progress * sign, -1.0) on the bottom straight."""
    sign = 1.0 if direction == 'ccw' else -1.0
    return (float(manifest.get('spawn_progress', -.25)) * sign, -1.0)


def _contact(world, clearance, x, y, now):
    kind = min(clearance, key=clearance.get)
    pillar = None
    if kind == 'pillar' and world.pillars:
        pillar = min(world.pillars, key=lambda p: math.hypot(p['x'] - x, p['y'] - y))['name']
    return dict(sim_time=now, wall_time=now, source='/audit/robot_contacts', pillar=pillar,
                other='game_field::field::wall_int' if kind == 'inner_wall' else
                      ('game_field::field::wall_ext' if kind == 'outer_wall' else
                       ('traffic_signs::' + (pillar or 'sign'))),
                kind=kind, robot='robotek::base_footprint::base_footprint_collision',
                max_depth=0.001, points=1, episode=0, end_sim_time=now, messages=1)


def _row(now, label, x, y, yaw, steer, direction):
    # The judge and the Gazebo telemetry call the final state DONE; the v2 mission calls it STOP.
    label = 'DONE' if label == 'STOP' else label
    return {'sim_time': now, 'wall_time': now, 'state': label, 'selected_direction': direction,
            'x_gt': x, 'y_gt': y, 'yaw_gt': yaw, 'steer_actual': steer, 'steer_right_actual': steer}


def _judge(world, direction, rows, events, contact, clearance, steer_max, trace):
    """Run the Gazebo judge on the lab trajectory written as a round directory."""
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        with (directory / 'telemetry.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['sim_time'])
            writer.writeheader()
            writer.writerows(rows)
        (directory / 'events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
        contacts = [contact] if contact else []
        (directory / 'contacts.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in contacts))
        # The judge only trusts wall contacts when the round's world carries the wall sensor.
        shutil.copyfile(world.directory / 'world.sdf', directory / 'world.sdf')
        _write_pillars_gt(directory, world, rows)
        manifest = {'scope': 'round', 'direction': direction, 'pillars': world.pillars,
                    'parking_lot': world.lot}
        report = summarize_full(directory, manifest)
    if trace:
        report['rows'] = rows
    return {'points': report['points_estimated'], 'time': report['rule_judge']['time_from_start_sim_seconds'],
            'valid': report['validation']['passed'], 'failed': report['validation']['failed'],
            'margin': report['validation']['margin_class'],
            'min_clearance': report['validation']['min_clearance_m'],
            'measured_clearance': min(clearance.values()) if clearance else None,
            'breakdown': report['points_breakdown_estimated'],
            'stop_validated': report.get('stop_validated'),
            'stop_in_start': report.get('stop_in_start_section'),
            'faults': report['rule_judge']['faults'],
            'parking': report.get('parking')}


def _write_pillars_gt(directory, world, rows):
    """Static sign ground truth, once per simulated second (the judge needs samples per sign)."""
    lines = []
    for row in rows[::10]:
        poses = [{'name': 'traffic_signs', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'yaw': 0.0}]
        for pillar in world.pillars:
            poses.append({'name': 'traffic_signs/' + pillar['name'], 'x': pillar['x'],
                          'y': pillar['y'], 'z': 0.05, 'yaw': 0.0})
        lines.append(json.dumps({'sim_time': row['sim_time'], 'poses': poses}) + '\n')
    (directory / 'pillars-gt.jsonl').write_text(''.join(lines))


# --------------------------------------------------------------------- CLI
def format_result(r):
    time = '%.2f' % r['time'] if r['time'] else '-'
    faults = ','.join(f['fault'] for f in r['faults'])
    return '%-10s pts=%-3s t=%-7s valid=%-5s %-10s m=%-6s contact=%-6s %s' % (
        r['direction'], r['points'], time, r['valid'], r['margin'],
        '%.1fcm' % (r['measured_clearance'] * 100) if r['measured_clearance'] is not None else '-',
        '%.1f' % r['contact_time'] if r['contact_time'] is not None else '-',
        faults or ','.join(r['failed']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--run', type=Path, default=DEFAULT_RUN, help='recorded round directory')
    parser.add_argument('--direction', choices=['ccw', 'cw'])
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--tmax', type=float, default=180.0)
    parser.add_argument('--param', action='append', default=[], help='name=value override')
    parser.add_argument('--strategy', default='v3', choices=['v3', 'v2', 'current'])
    parser.add_argument('--compare', action='store_true', help='print the recorded Gazebo round too')
    parser.add_argument('--out', type=Path, help='write the result as JSON')
    parser.add_argument('--no-occlusion', action='store_true', help='camera sees through boxes (before 26 oct 2026)')
    parser.add_argument('--car', choices=sorted(CARS), help='car profile (default: the Gazebo car, as before); '
                        'real_v2 = the real car of 4 nov 2026, real_v3 = the real car since 8 nov 2026, '
                        'real_v4 = since 11 nov 2026 (LD19 layout 0..2 pi, wider turns)')
    parser.add_argument('--car-param', action='append', default=[], help='name=value override of the car profile')
    args = parser.parse_args(argv)
    overrides = {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.param)}
    car = car_profile(args.car, {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.car_param)}) \
        if args.car else None
    result = run_round(args.run, args.direction, seed=args.seed, tmax=args.tmax, overrides=overrides,
                       strategy_name=args.strategy, occlusion=not args.no_occlusion, car=car)
    print(format_result(result), flush=True)
    if args.compare:
        recorded = (args.run / 'round.json')
        if recorded.exists():
            data = json.loads(recorded.read_text())
            judge = data.get('rule_judge') or {}
            print('gazebo    pts=%-3s t=%-7.2f valid=%s %s' % (
                data.get('points_estimated'), judge.get('time_from_start_sim_seconds') or -1,
                (data.get('validation') or {}).get('passed'),
                ','.join((data.get('validation') or {}).get('failed') or [])), flush=True)
    if args.out:
        args.out.write_text(json.dumps(result, indent=1, default=float))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
