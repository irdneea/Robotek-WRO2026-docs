#!/usr/bin/env python3
"""Replay recorded Obstacle rounds through the reference code and the refactored code.

Each round directory needs trace.jsonl.gz (IMU, scan and image events plus the
outputs of every control cycle, in callback order) and scans.jsonl.gz. The
reference package is extracted from a git commit. Both replays mirror their own
node's logic without ROS; camera lines are injected from the recorded direction.

  check_obstacle_refactor_equivalence.py --ref be3800d RUN_DIR [RUN_DIR ...]

Checks: (1) the reference replay reproduces the recorded commands (validates the
harness), (2) the refactored replay matches the reference replay on every cycle.
"""
import argparse
import gzip
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parents[3]
PKG = 'src/robotek_control/robotek_control'
STATE_ALIASES = {'FOLLOW': 'DIRECTION_SET'}  # one cycle after a camera decision


def load_reference(commit, directory):
    package = Path(directory)/'ref_robotek_control'
    package.mkdir()
    (package/'__init__.py').write_text('')
    names = subprocess.run(['git', 'ls-tree', '--name-only', commit, PKG + '/'], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split()
    for name in names:
        if name.endswith('.py'):
            source = subprocess.run(['git', 'show', f'{commit}:{name}'], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout
            (package/Path(name).name).write_text(source)
    sys.path.insert(0, str(directory))
    return package.name


def load_round(run):
    events = [json.loads(line) for line in gzip.open(run/'trace.jsonl.gz', 'rt') if line.strip()]
    scans = {}
    for line in gzip.open(run/'scans.jsonl.gz', 'rt'):
        if not line.strip():
            continue
        s = json.loads(line)
        scans[s['stamp']] = SimpleNamespace(
            angle_min=s['angle_min'], angle_increment=s['angle_increment'],
            range_min=s['range_min'], range_max=s['range_max'],
            ranges=[math.inf if v is None else v for v in s['ranges']])
    params = yaml.safe_load((run/'params.yaml').read_text())['obstacle_strategy']['ros__parameters']
    return events, scans, params


class ReferenceReplay:
    """Logic of obstacle_strategy_node at the reference commit (full_round, planner)."""

    def __init__(self, ref, params):
        nav = importlib.import_module(ref + '.obstacle_navigation')
        cfg = importlib.import_module(ref + '.obstacle_nav_config')
        perception = importlib.import_module(ref + '.obstacle_perception')
        odometry = importlib.import_module(ref + '.open_lidar_odometry')
        constants = importlib.import_module(ref + '.open_constants')
        merged = {f: getattr(cfg.ObstacleNavConfig(), f) for f in cfg.ObstacleNavConfig.__dataclass_fields__}
        merged.update({k: v for k, v in params.items() if k in merged})
        self.navigation = nav.ObstacleNavigation(merged)
        self.memory = perception.ObstacleMemory()
        self.wrap = perception.wrap
        self.lidar_odom = odometry.LidarOdometry(accel=constants.DISTANCE_MODEL_ACCEL)
        self.odom = (0., 0.)
        self.yaw = self.gyro = 0.
        self.yaw_zero = None
        self.imu_ready = False
        self.scan = None
        self.scan_stamp = self.image_stamp = self.imu_stamp = -math.inf
        self._imu_time = None
        self._last_speed = 0.
        self.state = 'WAIT_SENSORS'
        self.started = None

    def imu(self, t, wz):
        bias = self.navigation.controller.gyro_bias
        if self._imu_time is not None and 0. < t-self._imu_time < .2:
            self.yaw += (wz-bias)*(t-self._imu_time)
        self._imu_time = t
        self.gyro = wz
        self.imu_ready = True
        self.imu_stamp = t

    def on_scan(self, t, msg):
        self.scan, self.scan_stamp = msg, t
        self.lidar_odom.scan(msg, self.yaw)

    def image(self, t, obs, vis):
        self.image_stamp = t
        self.navigation.vision.direction = vis
        self.navigation.observe(obs)

    def tick(self, now):
        self.lidar_odom.command(self._last_speed, .02)
        step = self.lidar_odom.read()
        if not (self.yaw_zero is None or (abs(self._last_speed) < .01 and abs(self.lidar_odom.speed_model) < .01)):
            heading = self.yaw-self.yaw_zero
            sign = -1. if self._last_speed < 0 else 1.
            self.odom = (self.odom[0]+sign*step*math.cos(heading), self.odom[1]+sign*step*math.sin(heading))
        speed = steer = 0.
        fresh = self.imu_ready and all(0 <= now-s < .35 for s in (self.scan_stamp, self.image_stamp, self.imu_stamp))
        if self.started is None and fresh:
            self.started, self.yaw_zero, self.state = now, self.yaw, 'CALIBRATE'
        if self.started is not None and self.state not in ('DONE', 'FAULT'):
            if now-self.started > 180:
                self.state = 'FAULT'
            elif not fresh:
                self.state = 'WAIT_SENSOR'
            else:
                speed, steer, self.state = self.navigation.step(
                    now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, self.odom, self.memory)
                if self.state == 'DIRECTION_FAULT':
                    self.state = 'FAULT'
        w = speed*math.tan(steer)/.13
        self._last_speed = speed
        return speed, w, self.state


class RefactoredReplay:
    """Logic of the current obstacle_strategy_node (sensors -> ObstacleMission)."""

    def __init__(self, params):
        from robotek_obstacle import obstacle_strategy_node as node
        from robotek_obstacle.obstacle_config import ObstacleConfig
        from robotek_obstacle.obstacle_mission import ObstacleMission
        from robotek_common.vehicle import DISTANCE_MODEL_ACCEL
        from robotek_common.lidar_odometry import LidarOdometry
        from dataclasses import fields as dataclass_fields
        fields = {f.name for f in dataclass_fields(ObstacleConfig)}
        self.node = node
        self.mission = ObstacleMission(ObstacleConfig(**{k: v for k, v in params.items() if k in fields}))
        self.lidar_odom = LidarOdometry(accel=DISTANCE_MODEL_ACCEL)
        self.yaw = self.gyro = 0.
        self.yaw_zero = None
        self._imu_time = None
        self._last_speed = 0.
        self.scan = None
        self.scan_stamp = self.image_stamp = self.imu_stamp = -math.inf
        self.state = 'WAIT_SENSORS'
        self.started = None

    def imu(self, t, wz):
        if self._imu_time is not None and 0. < t-self._imu_time < .2:
            self.yaw += (wz-self.mission.gyro_bias)*(t-self._imu_time)
        self._imu_time = t
        self.gyro = wz
        self.imu_stamp = t

    def on_scan(self, t, msg):
        self.scan, self.scan_stamp = msg, t
        self.lidar_odom.scan(msg, self.yaw)

    def image(self, t, obs, vis):
        self.image_stamp = t
        self.mission.lines.direction = vis
        self.mission.observe(obs)

    def tick(self, now):
        node = self.node
        self.lidar_odom.command(self._last_speed, node.CONTROL_PERIOD)
        step = self.lidar_odom.read()
        distance = 0. if (self.yaw_zero is None or (abs(self._last_speed) < .01
                                                     and abs(self.lidar_odom.speed_model) < .01)) else step
        speed = steer = 0.
        fresh = (self._imu_time is not None
                 and all(0 <= now-t < node.SENSOR_MAX_AGE for t in (self.scan_stamp, self.image_stamp, self.imu_stamp)))
        if self.started is None and fresh:
            self.started, self.yaw_zero, self.state = now, self.yaw, 'CALIBRATE'
        if self.started is not None and self.state not in ('DONE', 'FAULT'):
            if now-self.started > node.ROUND_LIMIT:
                self.state = 'FAULT'
            elif not fresh:
                self.state = 'WAIT_SENSOR'
            else:
                speed, steer, self.state = self.mission.step(
                    now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, distance)
                if self.state == 'DIRECTION_FAULT':
                    self.state = 'FAULT'
        w = speed*math.tan(steer)/node.WHEELBASE
        self._last_speed = speed
        return speed, w, self.state


def replay(machine, events, scans):
    out = []
    for e in events:
        if e['k'] == 'imu':
            machine.imu(e['t'], e['wz'])
        elif e['k'] == 'scan':
            machine.on_scan(e['t'], scans[e['t']])
        elif e['k'] == 'img':
            machine.image(e['t'], e['obs'], e['vis'])
        elif e['k'] == 'tick':
            out.append(machine.tick(e['now']))
    return out


def compare(a, b, tolerance):
    """First differing cycle and the largest command difference."""
    worst = 0.
    for i, ((v1, w1, s1), (v2, w2, s2)) in enumerate(zip(a, b)):
        worst = max(worst, abs(v1-v2), abs(w1-w2))
        if STATE_ALIASES.get(s1, s1) != STATE_ALIASES.get(s2, s2) or abs(v1-v2) > tolerance or abs(w1-w2) > tolerance:
            return i, worst
    return (None if len(a) == len(b) else min(len(a), len(b))), worst


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ref', default='be3800d')
    parser.add_argument('--tolerance', type=float, default=1e-9)
    parser.add_argument('--output', type=Path)
    parser.add_argument('runs', nargs='+', type=Path)
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        ref = load_reference(args.ref, tmp)
        for run in args.runs:
            events, scans, params = load_round(run)
            recorded = [(e['v'], e['w'], e['state']) for e in events if e['k'] == 'tick']
            reference = replay(ReferenceReplay(ref, params), events, scans)
            refactored = replay(RefactoredReplay(params), events, scans)
            harness, _ = compare(recorded, reference, args.tolerance)
            equal, worst = compare(reference, refactored, args.tolerance)
            row = dict(run=run.name, cycles=len(recorded), states=sorted({s for _, _, s in recorded}),
                       reference_reproduces_recording=harness is None, reference_first_difference=harness,
                       refactored_equals_reference=equal is None, refactored_first_difference=equal,
                       max_command_difference=worst)
            results.append(row)
            print(json.dumps(row), flush=True)
    if args.output:
        args.output.write_text(json.dumps(dict(reference=args.ref, tolerance=args.tolerance, runs=results), indent=2)+'\n')
    sys.exit(0 if all(r['reference_reproduces_recording'] and r['refactored_equals_reference'] for r in results) else 1)


if __name__ == '__main__':
    main()
