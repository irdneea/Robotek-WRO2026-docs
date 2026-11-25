"""Open lab: the whole Open round in a few seconds, without Gazebo.

A closed-loop simulator for comparing Open strategies fast, built from the same pieces
the Gazebo runs use so that its results can be checked against them:

* the real field geometry (the wall boxes of the SDF), with ray casting for the LiDAR and
  a collision / clearance test of the car outline against the walls;
* the actuators of the real car: the same slew, delay, lag and speed table of
  ``sim_actuator_model`` with the values of ``real_car_v1.yaml`` (and the wheelbase default
  that model really uses in Gazebo), or with ``--car real_v2`` the car as it ran on 4 nov 2026
  (``real_car_v2.yaml``: motor_type 2 speed curve and rps cap, the real wheelbase, one scan per
  stamp and the v5 control loop running slower than the 50 Hz its gyro integration assumes);
* the LD19 scan of ``real_car:=true`` (10 Hz, 306 rays over +-110 deg, 8 mm noise, 4.3 %
  dropouts), a 50 Hz gyroscope with bias and noise, a 6 fps camera that knows the direction
  after ``camera_delay`` seconds;
* the rule judge of the Gazebo rounds (``judge_open`` and ``standard_validation``) applied to
  the lab trajectory, so points, stop and validity mean the same thing.

What it does NOT model: wheel slip, the Ackermann plugin dynamics, camera images, contact
forces (a contact ends the round) or the motor under load. Results must be compared with
Gazebo on the standard set before they are used to decide anything (``--compare``).

    python3 -m robotek_evaluation.open_lab --suite std12 --tag lab-v5
"""
import argparse
import itertools
import json
import math
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from robotek_common import vehicle
from .rule_judge import judge_open, standard_validation
from .sim_actuator_model import slew, table_speed, wheel_angle

ROOT = Path(__file__).resolve().parents[3]
FIELDS = ROOT / 'docs' / 'open-challenge-runs' / 'field-size-driver' / 'worlds'
STD12 = tuple((field, direction) for field in (
    'square100', 'square180', 'rect100x180', 'rect180x100', 'shift140', 'east140x100')
    for direction in ('ccw', 'cw'))
# The classic field (square island, 1 m corridors) in both directions: the fast check of the real_v2 car.
CLASSIC = (('square100', 'ccw'), ('square100', 'cw'))
# The rules' 16 island layouts (each side's corridor 1.0 or 0.6 m; tools/make_open_centres.py) in both directions.
CENTRES = tuple((f"../worlds-centres/c{''.join(c)}", direction)
                for c in itertools.product('WN', repeat=4) for direction in ('ccw', 'cw'))
SUITES = {'std12': STD12, 'classic': CLASSIC, 'centres': CENTRES}
START = (0.0, -1.15)

PHYSICS_HZ = 100.0          # the actuator model runs at 100 Hz in Gazebo too
CONTROL_EVERY = 2           # 50 Hz strategy
SCAN_EVERY = 10             # 10 Hz LiDAR
IMU_EVERY = 2               # 50 Hz gyroscope
CAMERA_PERIOD = 1.0 / 6.0
TELEMETRY_EVERY = 10        # 10 Hz rows for the judge, as the Gazebo telemetry
SCAN_RAYS = 306
SCAN_HALF_ANGLE = math.radians(110.0)
SCAN_MIN_RANGE = 0.12
SCAN_NOISE = 0.008
SCAN_DROPOUT = 0.043
# The Gazebo runs deliver every LiDAR stamp three times (recorded scans: 30 messages/s for a 10 Hz
# sensor), each copy with its own dropouts.
SCAN_COPIES = 3
GYRO_NOISE = 0.0019
GYRO_BIAS = 0.006
# Optional first-order lag between the actuator model's yaw rate and the body's. Off by default: against
# the Gazebo ground truth the yaw rate follows the measured wheel angle with no lag (rms 0.03 rad/s);
# the lag that exists is in the wheel itself. A fit of 0.05 s lowers the open-loop error but makes
# the baseline rounds 1.5 s slower than Gazebo, so it is left to experiments.
PLANT_TAU = 0.0
CAMERA_DELAY = 0.3          # s after Start until the camera has confirmed the direction (Gazebo: before 0.44 s)
STOP_DEAD_DECEL = 50.0      # m/s^2: the adapter's command without its ramp (stop_dead); the motor model still lags
STOP_HOLD = 31.0            # the judge needs the stop observed for 30 s


# ------------------------------------------------------------------- world
class World:
    """Axis-aligned wall boxes read from an Open field SDF."""

    def __init__(self, path):
        link = ET.parse(path).find(".//model[@name='game_field']/link[@name='field']")
        boxes, kinds = [], []
        for node in link.findall('collision'):
            name = node.get('name', '')
            if not name.startswith('wall_'):
                continue
            pose = [float(v) for v in node.findtext('pose').split()]
            size = [float(v) for v in node.findtext('geometry/box/size').split()]
            boxes.append((pose[0] - size[0] / 2, pose[0] + size[0] / 2,
                          pose[1] - size[1] / 2, pose[1] + size[1] / 2))
            kinds.append('inner_wall' if name.startswith('wall_int') else 'outer_wall')
        self.boxes = np.array(boxes)
        self.kinds = kinds
        self.path = Path(path)
        from .open_field_geometry import field_geometry
        self.geometry = field_geometry(path)

    def raycast(self, ox, oy, angles):
        """Distance from (ox, oy) along each angle to the nearest wall box (inf if none)."""
        dx, dy = np.cos(angles), np.sin(angles)
        best = np.full(angles.shape, np.inf)
        with np.errstate(divide='ignore', invalid='ignore'):
            for xmin, xmax, ymin, ymax in self.boxes:
                tx = np.stack([(xmin - ox) / dx, (xmax - ox) / dx])
                ty = np.stack([(ymin - oy) / dy, (ymax - oy) / dy])
                near = np.maximum(tx.min(axis=0), ty.min(axis=0))
                far = np.minimum(tx.max(axis=0), ty.max(axis=0))
                # A ray that starts inside a box (the car touching a wall) does not see it.
                hit = (far >= near) & (near > 1e-6)
                best = np.where(hit & (near < best), near, best)
        return best

    def clearances(self, polygon):
        """(outer, inner) smallest distance from the car outline to each kind of wall; <= 0 touches."""
        out = {'outer_wall': math.inf, 'inner_wall': math.inf}
        samples = _perimeter(polygon, 0.02)
        for (xmin, xmax, ymin, ymax), kind in zip(self.boxes, self.kinds):
            dx = np.maximum(np.maximum(xmin - samples[:, 0], samples[:, 0] - xmax), 0.0)
            dy = np.maximum(np.maximum(ymin - samples[:, 1], samples[:, 1] - ymax), 0.0)
            distance = float(np.hypot(dx, dy).min())
            corners = np.array([(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)])
            if _inside(polygon, corners).any():
                distance = 0.0
            out[kind] = min(out[kind], distance)
        return out


def _perimeter(polygon, step):
    points = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        count = max(2, int(math.dist(a, b) / step))
        for i in range(count):
            f = i / count
            points.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return np.array(points)


def _inside(polygon, points):
    """Points inside a convex counter-clockwise polygon."""
    inside = np.ones(len(points), dtype=bool)
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        cross = (b[0] - a[0]) * (points[:, 1] - a[1]) - (b[1] - a[1]) * (points[:, 0] - a[0])
        inside &= cross >= 0.0
    return inside


def outline(x, y, yaw):
    """Car outline (counter-clockwise) from the measured overall dimensions."""
    c, s = math.cos(yaw), math.sin(yaw)
    corners = [(vehicle.OUTLINE_FRONT, -vehicle.OUTLINE_HALF_WIDTH),
               (vehicle.OUTLINE_FRONT, vehicle.OUTLINE_HALF_WIDTH),
               (-vehicle.OUTLINE_REAR, vehicle.OUTLINE_HALF_WIDTH),
               (-vehicle.OUTLINE_REAR, -vehicle.OUTLINE_HALF_WIDTH)]
    return [(x + px * c - py * s, y + px * s + py * c) for px, py in corners]


# --------------------------------------------------------------- actuators
CONFIG = Path(__file__).resolve().parents[1] / 'config'
# Lab car profiles: real_v1 is the car of Gazebo real_car:=true (measured 8 oct 2026), real_v2 the real car
# as it ran on 4 nov 2026 (runaway motor_type 2), real_v3 the real car since 8 nov 2026 (speed-controlled motor on
# M2, 54:30 gears) (docs/open-estado.md, section "Perfiles del coche en el lab").
CARS = {'real_v1': 'real_car_v1.yaml', 'real_v2': 'real_car_v2.yaml', 'real_v3': 'real_car_v3.yaml',
        'real_v4': 'real_car_v4.yaml'}
# Lab-only keys of a profile's ``lab:`` section that act on the actuators (0 = off).
LAB_ACTUATOR_KEYS = ('stall_steer', 'brake_delay', 'brake_decel', 'brake_imu_gap', 'understeer', 'no_turn_lock',
                     'no_turn_s', 'drive_min_speed', 'drive_min_on_stop', 'drive_gain', 'lock_speed_factor',
                     'counter_speed', 'counter_s', 'kick_speed', 'kick_s', 'kick_after', 'lock_breakaway')


def actuator_parameters(path=None, gazebo_servo=True):
    """The sim_actuator_model parameters of the real car, with that node's own defaults."""
    path = path or CONFIG / 'real_car_v1.yaml'
    values = yaml.safe_load(Path(path).read_text())['sim_actuator_model']['ros__parameters']
    if gazebo_servo:
        # Measured in Gazebo with scripted steering steps (docs/open-lab.md): the wheel starts moving 0.10 s
        # after the command (the model's 0.06 s plus the plugin's) and follows with a 0.06 s lag.
        values = {**values, 'steer_delay': 0.10, 'steer_tau': 0.06}
    defaults = dict(wheelbase=0.13, steer_limit=0.4363323129985824, steer_delay=0.03,
                    steer_rate=4.4, steer_tau=0.03, accel_max=2.0, decel_max=2.0,
                    drive_delay=0.0, drive_tau=0.0, drive_command_limit=0.0, drive_deadband=0.0,
                    speed_table_cmd=[0.0], speed_table_real=[0.0], stall_steer=0.0)
    return {**defaults, **values}


def car_profile(name='real_v1', overrides=None):
    """Lab car: actuator parameters plus the lab-only options (control_hz, scan_copies). ``overrides``
    (name -> value) replace either kind."""
    path = CONFIG / CARS[name]
    lab = yaml.safe_load(path.read_text()).get('lab') or {}
    actuator = actuator_parameters(path, gazebo_servo=name == 'real_v1')
    for key in LAB_ACTUATOR_KEYS:
        actuator[key] = float(lab.get(key, 0.0))
    car = {'name': name, 'actuator': actuator, 'control_hz': lab.get('control_hz'),
           'scan_copies': int(lab.get('scan_copies', SCAN_COPIES)), 'measured_dt': bool(lab.get('measured_dt', False)),
           'scan_gap_rate': float(lab.get('scan_gap_rate', 0.0)), 'scan_gap_max': float(lab.get('scan_gap_max', 0.0)),
           # the gyro reads this share of the real yaw rate (the car, 4 nov 2026: 4-6 deg short per corner = ~0.94)
           'gyro_scale': float(lab.get('gyro_scale', 1.0)),
           # base_adapter's no_ramp_states for the end of the round: in FINISH and DONE the speed command is not
           # ramped down (decel_limit), it goes to the motor at once
           'stop_dead': bool(lab.get('stop_dead', False)),
           # the scan message as the car's LD19 gives it: FULL_CIRCLE_RAYS rays, angles 0..2 pi (the Gazebo LD19 and
           # the lab give -110..+110 deg). Clockwise the v5 never found the island wall with it (11 nov 2026).
           'scan_full_circle': bool(lab.get('scan_full_circle', False))}
    for key, value in (overrides or {}).items():
        if key in ('control_hz', 'scan_copies', 'measured_dt', 'scan_gap_rate', 'scan_gap_max', 'gyro_scale', 'stop_dead',
                   'scan_full_circle'):
            car[key] = value
        elif key in actuator:
            actuator[key] = value
        else:
            raise KeyError(f'unknown car parameter {key}')
    return car


class Actuators:
    """Python mirror of SimActuatorModel: servo with dead time, rate and lag; motor with slew,
    dead time, speed table and lag. Input: speed and steering commands. Output: speed and yaw rate."""

    def __init__(self, params=None):
        self.p = params or actuator_parameters()
        cmd = [float(x) for x in self.p['speed_table_cmd'] if float(x) > 0.0]
        real = [float(x) for x in self.p['speed_table_real']][-len(cmd):] if cmd else []
        self.table = (cmd, real)
        self.v_cmd = self.steer_cmd = 0.0
        self.v = self.steer = self.v_out = 0.0
        self.target = 0.0
        self.steer_queue, self.drive_queue = [], []
        self.delayed_v = 0.0
        self.zero_since = None         # when the speed command went to 0 after moving (brake_decel)
        self.locked = False            # the wheels at full lock (no_turn_lock counts these episodes)
        self.lock_episodes = 0
        self.no_turn_until = -math.inf
        self.counter = None            # (until, speed) of a counter-pulse brake (counter_speed > 0)
        self.kick = None               # (until, speed) of a start kick (kick_speed > 0)
        self.stopped_at = -math.inf    # when the speed command last went to 0

    def command(self, now, speed, steer):
        p = self.p
        if (abs(speed) >= p['drive_deadband'] and abs(self.v_cmd) < p['drive_deadband']
                and p.get('kick_speed', 0.0) > 0.0 and now - self.stopped_at >= p.get('kick_after', 0.5)):
            # base_adapter's start kick (robotek-learn motor_kick_rps / motor_kick_s): from a standstill of at least
            # kick_after s, at least kick_speed (m/s asked) for kick_s s.
            self.kick = (now + p.get('kick_s', 0.2), math.copysign(p['kick_speed'], speed))
        if abs(speed) < p['drive_deadband'] <= abs(self.v_cmd):   # the motor stops (the servo creep is below it)
            self.stopped_at = now
            self.kick = None
        if abs(speed) < 1e-3 and abs(self.v_cmd) >= 1e-3:
            self.zero_since = now
            if self.p.get('counter_speed', 0.0) > 0.0 and abs(self.v_cmd) >= self.p['drive_deadband']:
                # Counter-pulse brake (8 nov floor test): the opposite speed for counter_s s, then 0.
                self.counter = (now + self.p.get('counter_s', 0.15), -math.copysign(self.p['counter_speed'], self.v_cmd))
        elif abs(speed) >= 1e-3:
            self.zero_since = self.counter = None
        self.v_cmd = speed
        if abs(speed) > 1e-3:
            # The node turns (v, steer) into a Twist, the model back into a steering angle with
            # its own wheelbase.
            wz = speed * math.tan(steer) / vehicle.WHEELBASE
            self.steer_cmd = math.atan(wz * self.p['wheelbase'] / speed)
        self.steer_queue.append((now, self.steer_cmd))

    def step(self, now, dt):
        p = self.p
        target = None
        while self.steer_queue and now - self.steer_queue[0][0] >= p['steer_delay']:
            target = self.steer_queue.pop(0)[1]
        if target is not None:
            self.target = max(-p['steer_limit'], min(p['steer_limit'], target))
        change = self.target - self.steer
        if p['steer_tau'] > 0.0:
            change *= min(1.0, dt / p['steer_tau'])
        limit = p['steer_rate'] * dt
        self.steer += max(-limit, min(limit, change))
        if p.get('brake_decel', 0.0) > 0.0 and self.zero_since is not None \
                and now - self.zero_since >= p.get('brake_delay', 0.0):
            # The real car's stop (robotek-learn base_adapter brake_reset): the board is reset and the car slows
            # down at brake_decel, whatever the motor model was doing.
            self.v = self.delayed_v = 0.0
            self.drive_queue.clear()
            self.v_out = math.copysign(max(0.0, abs(self.v_out) - p['brake_decel'] * dt), self.v_out)
            return self.v_out, self.yaw_rate(now, self.v_out)
        self.v = slew(self.v, self.v_cmd, p['accel_max'], p['decel_max'], dt)
        v = self.v
        if self.kick is not None:
            if now < self.kick[0]:
                v = math.copysign(max(abs(v), abs(self.kick[1])), self.kick[1])
            else:
                self.kick = None
        if self.counter is not None:
            if now < self.counter[0]:
                v = self.v = self.counter[1]   # the adapter's ramp starts again from 0 after the pulse
            else:
                v = self.v = 0.0
                self.counter = None
        elif p.get('drive_min_speed', 0.0) > 0.0 and abs(v) >= p['drive_deadband']:
            # robotek-learn base_adapter motor_min_rps, before the board's delay: any command it sends, also while it
            # ramps a stop down to 0, is at least this (m/s asked); only a plain 0 stops the motor. drive_min_on_stop
            # 0: a 0 command cuts the floored motor at once.
            if abs(self.v_cmd) < 1e-3 and p.get('drive_min_on_stop', 1.0) <= 0.0:
                v = 0.0
            else:
                v = math.copysign(max(abs(v), p['drive_min_speed']), v)
        if p['drive_delay'] > 0.0:
            self.drive_queue.append((now, v))
            v = None
            while self.drive_queue and now - self.drive_queue[0][0] >= p['drive_delay']:
                v = self.drive_queue.pop(0)[1]
            self.delayed_v = self.delayed_v if v is None else v
            v = self.delayed_v
        if p['drive_command_limit'] > 0.0:
            v = max(-p['drive_command_limit'], min(p['drive_command_limit'], v))
        if abs(v) < p['drive_deadband']:
            v = 0.0
        if (p.get('lock_breakaway', 0.0) > 0.0 and abs(self.steer) >= 0.9 * p['steer_limit']
                and abs(self.v_out) < 0.01 and abs(v) < p['lock_breakaway']):
            # Standing at full lock the motor needs at least lock_breakaway (m/s asked) to move the car (8 nov:
            # 1.1 rps alone sometimes did not, the 2 rps start kick did); once it rolls, less keeps it going.
            v = 0.0
        v = table_speed(v, *self.table)
        if p.get('drive_gain', 0.0) > 0.0:
            v *= p['drive_gain']       # real speed / table speed (0 = off): the 8 nov floor brake test at 1.2 rps
        if 0.0 < p.get('lock_speed_factor', 0.0) < 1.0:
            # The wheels scrub at full lock: the car covers this fraction of the straight distance (0 = off).
            v *= 1.0 - (1.0 - p['lock_speed_factor']) * min(1.0, abs(self.steer) / p['steer_limit'])
        if p.get('stall_steer', 0.0) > 0.0 and abs(self.steer) >= p['stall_steer']:
            v = 0.0                    # the motor cannot move the car with the wheels at full lock
        if p['drive_tau'] > 0.0:
            self.v_out += (v - self.v_out) * min(1.0, dt / p['drive_tau'])
        else:
            self.v_out = v
        return self.v_out, self.yaw_rate(now, self.v_out)

    def yaw_rate(self, now, v):
        """Yaw rate of the bicycle model for the servo angle self.steer, with the optional real-car terms:
        steer_gain / steer_deadband (as SimActuatorModel), understeer (the curvature divided by
        1 + understeer * v^2) and the no-turn fault (the no_turn_lock-th time the wheels reach full lock they
        give no yaw for no_turn_s s, whatever is commanded: real car 4 nov tests 19/27 and 8 nov Open round 3)."""
        p = self.p
        if p.get('no_turn_lock', 0.0) > 0.0:
            limit = p['steer_limit']
            if not self.locked and abs(self.steer) >= 0.95 * limit:
                self.locked = True
                self.lock_episodes += 1
                if self.lock_episodes == int(p['no_turn_lock']):
                    self.no_turn_until = now + p.get('no_turn_s', 0.0)
            elif self.locked and abs(self.steer) < 0.8 * limit:
                self.locked = False
            if now < self.no_turn_until:
                return 0.0
        wheel = wheel_angle(self.steer, p.get('steer_deadband', 0.0), p.get('steer_gain', 1.0))
        rate = v * math.tan(wheel) / p['wheelbase']
        if p.get('understeer', 0.0) > 0.0:
            rate /= 1.0 + p['understeer'] * v * v
        return rate


# ---------------------------------------------------------------- strategy
class V5Strategy:
    """The Open v5 mission (robotek_open.v5) wired as its node will be: one Scene per distinct LiDAR stamp."""

    def __init__(self, params=None):
        from robotek_open.v5.mission import OpenMission
        from robotek_open.v5.scene import Scene
        self.mission = OpenMission(params)
        self._scene, self._stamp, self._started = Scene(), None, False
        self._gyro, self._camera = 0.0, 0

    def on_scan(self, scan):
        from robotek_open.v5.scene import scene_from_scan
        stamp = (scan.header.stamp.sec, scan.header.stamp.nanosec)
        if stamp != self._stamp:                       # the later copies of a stamp are dropped
            self._stamp = stamp
            self._scene = scene_from_scan(scan, self.mission.forward_yaw, self.mission.direction or 'ccw')
        first = not self._started
        if first:
            self._started = True
            self.mission.request_start()
        return first

    def on_imu(self, now, gyro_z):
        self._gyro = gyro_z

    def on_camera(self, direction):
        self._camera = direction

    # The node's stale-LiDAR brake (robotek_open/v5/node.py, scan_max_age in the car's car_picam.yaml): a scan older
    # than this -> 0, 0 after the mission step (the gyro keeps integrating). Only matters with scan_gap_rate.
    SCAN_MAX_AGE = 1.0

    def control(self, dt, camera_age, scan_age=0.0):
        camera = self._camera if camera_age <= 0.5 else 0
        speed, steer = self.mission.step(dt, self._scene, self._gyro, camera)
        if scan_age > self.SCAN_MAX_AGE:
            speed, steer = 0.0, 0.0
        return speed, steer

    @property
    def label(self):
        return self.mission.label

    @property
    def turns(self):
        return self.mission.completed

    @property
    def done(self):
        return self.mission.state == 'STOP'

    @property
    def stop_label(self):
        return self.mission.label if self.done else None


def v5_factory(overrides=None):
    """Factory of V5Strategy; ``overrides`` replace the mission parameters."""
    from robotek_open.v5.mission import Params
    return lambda: V5Strategy(Params(**(overrides or {})))


# ------------------------------------------------------------------- round
FULL_CIRCLE_RAYS = 504     # the car's LD19: one turn at ~0.71 deg per ray


def full_circle(ranges, angle_min, increment):
    """The same rays in the car's message layout: (ranges, angle_min, increment) with angles 0..2 pi."""
    step = 2.0 * math.pi / FULL_CIRCLE_RAYS
    out = [math.inf] * FULL_CIRCLE_RAYS
    for k, value in enumerate(ranges):
        out[int(round(((angle_min + k * increment) % (2.0 * math.pi)) / step)) % FULL_CIRCLE_RAYS] = value
    return out, 0.0, step


def make_scan(ranges, now, angle_min, increment):
    from types import SimpleNamespace
    sec = int(now)
    return SimpleNamespace(
        ranges=ranges, angle_min=angle_min, angle_increment=increment, range_min=SCAN_MIN_RANGE,
        range_max=12.0, header=SimpleNamespace(stamp=SimpleNamespace(
            sec=sec, nanosec=int(round((now - sec) * 1e9)))))


def run_round(world, direction, strategy, seed=0, tmax=180.0, spawn=START, plant_tau=PLANT_TAU,
              actuator=None, scan_copies=None, trace=False, latency=0.0, car=None):
    """One round: ``strategy`` is a zero-argument factory, ``car`` a car_profile (None: real_v1).
    Returns the lab result dict."""
    rng = np.random.default_rng(seed)
    world = world if isinstance(world, World) else World(world)
    strategy = strategy()
    actuators = Actuators({**(car['actuator'] if car else actuator_parameters()), **(actuator or {})})
    if scan_copies is None:
        scan_copies = car['scan_copies'] if car else SCAN_COPIES
    # The strategy integrates with dt = CONTROL_EVERY / PHYSICS_HZ (1/50 s); with control_hz its ticks come at
    # that real rate instead (a slow loop on the Pi), and with measured_dt it gets the real time between ticks.
    control_hz = car.get('control_hz') if car else None
    measured_dt = bool(car and car.get('measured_dt'))
    control_slot, last_control = -1, None
    sign = 1.0 if direction == 'ccw' else -1.0
    yaw = 0.0 if direction == 'ccw' else math.pi
    # The car turns about its rear axle (bicycle model): the pose of base_link, at mid-wheelbase, slides
    # sideways by atan(REAR_AXLE_X*yaw_rate/v) (0.14 rad at full lock; measured in Gazebo).
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
    camera_time, camera_stamp = None, None
    camera_direction = 0
    contact = None
    clearance = {'outer_wall': math.inf, 'inner_wall': math.inf}
    steer_max = 0.0
    yaw_rate = 0.0
    stopped_at = None
    commanded_rate = 0.0
    pending = []
    gap_rate = car.get('scan_gap_rate', 0.0) if car else 0.0
    gyro_scale = car.get('gyro_scale', 1.0) if car else 1.0
    stop_dead = bool(car.get('stop_dead')) if car else False
    scan_full_circle = bool(car.get('scan_full_circle')) if car else False
    gap_max = car.get('scan_gap_max', 0.0) if car else 0.0
    gap_until, last_scan = -math.inf, 0.0
    for tick in range(int(tmax / dt)):
        now = tick * dt
        if tick % SCAN_EVERY == 0 and gap_rate > 0.0 and now >= gap_until and \
                rng.random() < gap_rate * SCAN_EVERY * dt:
            gap_until = now + rng.uniform(0.2, max(0.2, gap_max))   # the LD19 skips whole scans (11 nov 2026)
        if tick % SCAN_EVERY == 0 and now >= gap_until:
            last_scan = now
            ranges = world.raycast(x + vehicle.LIDAR_OFFSET_X * math.cos(yaw),
                                   y + vehicle.LIDAR_OFFSET_X * math.sin(yaw), beams + yaw)
            ranges = ranges + rng.normal(0.0, SCAN_NOISE, SCAN_RAYS)
            ranges[(ranges < SCAN_MIN_RANGE) | ~np.isfinite(ranges)] = math.inf
            for _ in range(scan_copies):
                copy = ranges.copy()
                copy[rng.random(SCAN_RAYS) < SCAN_DROPOUT] = math.inf
                message = full_circle(list(copy), angle_min, increment) if scan_full_circle \
                    else (list(copy), angle_min, increment)
                if strategy.on_scan(make_scan(message[0], now, *message[1:])):
                    t_start = now
                    events.append({'event': 'start', 'sim_time': now, 'wall_time': now})
        if tick % IMU_EVERY == 0:
            strategy.on_imu(now, gyro_scale * yaw_rate + bias + rng.normal(0.0, GYRO_NOISE))
        if t_start is not None and now >= t_start + CAMERA_DELAY and \
                (camera_time is None or now - camera_time >= CAMERA_PERIOD - 1e-9):
            camera_time = now
            camera_direction = int(sign)
            strategy.on_camera(camera_direction)
        if control_hz:
            slot = int(now * control_hz + 1e-9)
            due, control_slot = slot != control_slot, slot
        else:
            due = tick % CONTROL_EVERY == 0
        if due:
            age = math.inf if camera_time is None else now - camera_time
            step = dt * CONTROL_EVERY
            if measured_dt and last_control is not None:
                step = now - last_control
            last_control = now
            speed, steer = strategy.control(step, age, now - last_scan)
            pending.append((now + latency, speed, steer))
        while pending and pending[0][0] <= now + 1e-9:
            if stop_dead and strategy.label in ('FINISH', 'DONE'):
                actuators.p['decel_max'] = STOP_DEAD_DECEL
            actuators.command(now, *pending.pop(0)[1:])
        v_out, commanded_rate = actuators.step(now, dt)
        yaw_rate += (commanded_rate - yaw_rate) * (min(1.0, dt / plant_tau) if plant_tau > 0 else 1.0)
        yaw += yaw_rate * dt
        xr += v_out * math.cos(yaw) * dt
        yr += v_out * math.sin(yaw) * dt
        x, y = xr + back * math.cos(yaw), yr + back * math.sin(yaw)
        steer_max = max(steer_max, abs(actuators.steer))
        if tick % CONTROL_EVERY == 0:
            clearance = {k: min(clearance[k], v) for k, v in world.clearances(outline(x, y, yaw)).items()}
            if contact is None and min(clearance.values()) <= 0.0:
                contact = now
        if tick % TELEMETRY_EVERY == 0:
            rows.append(_row(now, strategy.label, x, y, yaw, actuators.steer))
        if contact is not None:
            break
        if strategy.done and stopped_at is None:
            stopped_at = now
            events.append({'event': 'done', 'sim_time': now, 'wall_time': now})
        if stopped_at is not None and abs(v_out) < 1e-3 and abs(yaw_rate) < 1e-3 \
                and now - stopped_at > 1.0:
            break
    last = rows[-1] if rows else None
    if stopped_at is not None and contact is None and last is not None:
        # Stopped for good: the car stays where it is while the judge's 30 s observation passes.
        count = int(STOP_HOLD * PHYSICS_HZ / TELEMETRY_EVERY)
        rows.extend(_row(last['sim_time'] + (i + 1) * TELEMETRY_EVERY / PHYSICS_HZ, last['state'],
                         x, y, yaw, actuators.steer) for i in range(count))
    result = _result(world, direction, strategy, rows, events, clearance, contact, steer_max, t_start)
    result['stop_pose'] = [round(x, 3), round(y, 3), round(math.degrees(yaw), 1)]   # where the round ended
    if trace:
        result['rows'] = rows
    return result


def _row(now, label, x, y, yaw, steer):
    return {'sim_time': now, 'wall_time': now, 'state': label, 'x_gt': x, 'y_gt': y, 'yaw_gt': yaw,
            'steer_actual': steer, 'steer_right_actual': steer}


def _result(world, direction, strategy, rows, events, clearance, contact, steer_max, t_start):
    with tempfile.TemporaryDirectory() as tmp:
        manifest = {'direction': direction, 'field_geometry': world.geometry}
        judge = judge_open(Path(tmp), manifest, rows, events)
        validation = standard_validation(
            judge, {k: (None if math.isinf(v) else v) for k, v in clearance.items()},
            contacts_evaluated=True, contacts_any=contact is not None,
            stop_hold=judge.get('stop_hold_sim_seconds'), steer_max_deg=math.degrees(steer_max))
    return {'field': world.path.stem, 'direction': direction, 'points': judge['points'],
            'time': judge['time_from_start_sim_seconds'], 'valid': validation['passed'],
            'failed': validation['failed'], 'margin': validation['margin_class'],
            'min_clearance': validation['min_clearance_m'], 'contact_time': contact,
            'end': strategy.stop_label or strategy.label, 'turns': strategy.turns,
            'laps': [lap['sim_seconds'] for lap in judge['lap_splits']],
            'breakdown': judge['breakdown'], 'stop_inside': judge.get('stop_inside_finish_section'),
            'stop_drift': judge.get('stop_drift_m')}


# --------------------------------------------------------------------- CLI
START_GRID_X = (-0.3, 0.0, 0.3)   # m along the start section, from its centre
START_GRID_WALL = 0.2             # m from each wall for the two side starts (the third is the corridor's centre)


def start_grid(world_path):
    """Nine starts in the south section: 3 along x 3 across (0.2 m from each wall and the centre). A change that held
    from the single default start broke from these (12 nov 2026: the final brake at full lock, the first corner)."""
    from .open_field_geometry import field_geometry
    geometry = field_geometry(world_path)
    low, high = geometry['outer']['ymin'], geometry['inner']['ymin']
    return [(x, round(y, 3)) for x in START_GRID_X
            for y in (low + START_GRID_WALL, (low + high) / 2, high - START_GRID_WALL)]


def run_suite(strategy, seed=0, fields=None, directions=None, worlds=FIELDS, car=None, spawn=START,
              suite=STD12, starts='one'):
    results = []
    for field, direction in suite:
        if (fields and field not in fields and Path(field).name not in fields) or (directions and direction not in directions):
            continue
        path = worlds / f'{field}.sdf'
        for start in (start_grid(path) if starts == 'grid' else [spawn]):
            result = run_round(path, direction, strategy, seed=seed, car=car, spawn=start)
            result['spawn'] = list(start)
            results.append(result)
    return results


def format_result(r):
    time = '%.2f' % r['time'] if r['time'] else '-'
    return '%-22s pts=%-3s t=%-7s valid=%-5s %-12s %s' % (
        f"{r['field']}-{r['direction']}" + ('@%g,%g' % tuple(r['spawn']) if tuple(r.get('spawn', START)) != START else ''), r['points'], time, r['valid'], r['margin'],
        ','.join(r['failed']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--suite', choices=sorted(SUITES),
                        help='std12 (default with real_v1), classic: square100 ccw and cw (default with real_v2 and real_v3), or centres: the 16 island layouts x 2 directions')
    parser.add_argument('--tag', default='lab')
    parser.add_argument('--strategy', default='v5', choices=['v5'], help='Open v5, the only strategy')
    parser.add_argument('--param', action='append', default=[], help='name=value override')
    parser.add_argument('--car', default='real_v1', choices=sorted(CARS),
                        help='real_v1: Gazebo real_car:=true (default); real_v2: the real car of 4 nov 2026; real_v3: since 8 nov 2026; real_v4: since 11 nov 2026 (wider turns, LiDAR gaps)')
    parser.add_argument('--car-param', action='append', default=[],
                        help='name=value override of the car profile (actuator or lab key)')
    parser.add_argument('--spawn', help='x,y of the start (default %s,%s); the yaw is the direction\'s' % START)
    parser.add_argument('--starts', choices=['one', 'grid'], default='one',
                        help='one: --spawn (default); grid: 9 starts per round, 3 along x 3 across the start section')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--field', action='append')
    parser.add_argument('--direction', action='append')
    parser.add_argument('--out', type=Path, help='write the results as JSON')
    parser.add_argument('--against', type=Path, help='previous --out JSON: print the change per round')
    parser.add_argument('--brief', action='store_true',
                        help='print only rounds whose points or validity changed (with --against), else only invalid ones')
    args = parser.parse_args(argv)
    overrides = {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.param)}
    factory = v5_factory(overrides)
    car = None
    if args.car != 'real_v1' or args.car_param:
        car = car_profile(args.car, {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.car_param)})
    spawn = tuple(float(v) for v in args.spawn.split(',')) if args.spawn else START
    suite = SUITES[args.suite or ('std12' if args.car == 'real_v1' else 'classic')]
    results = run_suite(factory, args.seed, args.field, args.direction, car=car, spawn=spawn, suite=suite,
                        starts=args.starts)
    previous = {}
    if args.against and args.against.exists():
        previous = {(r['field'], r['direction'], tuple(r.get('spawn', ()))): r
                    for r in json.loads(args.against.read_text())['rounds']}
    for result in results:
        old = previous.get((result['field'], result['direction'], tuple(result['spawn'])))
        if args.brief and ((old['points'], old['valid']) == (result['points'], result['valid'])
                           if old else result['valid']):
            continue
        change = f"  was {old['points']} {'valid' if old['valid'] else 'invalid'}" if old else ''
        print(format_result(result) + change, flush=True)
    valid = sum(r['valid'] for r in results)
    was = f" (was {sum(1 for r in results if previous.get((r['field'], r['direction'], tuple(r['spawn'])), {}).get('valid'))})" \
        if previous else ''
    times = [r['time'] for r in results if r['time']]
    print(f'{valid}/{len(results)} valid{was}, mean time {np.mean(times) if times else 0.0:.2f} s')
    if args.out:
        args.out.write_text(json.dumps({'tag': args.tag, 'seed': args.seed, 'car': args.car,
                                        'car_param': args.car_param, 'rounds': results}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
