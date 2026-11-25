#!/usr/bin/env python3
"""Run one recorded Obstacle round: three laps on a regulation layout, or parking only.

Preparation (world, signs, audit sensors, parameters, snapshot) is in
robotek_evaluation.obstacle_experiment_setup; the report in obstacle_full_round_report.
Every attempt, also failed ones, is saved in docs/obstacle-challenge-runs/.
"""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from robotek_evaluation.obstacle_experiment_setup import prepare_round, write_json
from robotek_evaluation.obstacle_full_round_report import pillar_outside_circle, summarize_full
from robotek_evaluation.obstacle_parking_report import summarize_parking
from robotek_evaluation.open_experiment_analysis import merge_audit_pose

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT/'docs/obstacle-challenge-runs'


def summarize(directory, manifest):
    if manifest.get('scope') == 'parking':
        return summarize_parking(directory, manifest)
    return summarize_full(directory, manifest)


def watch_for_round_fault(proc, directory, seats, timeout, stop_on_fault=True, grace=3.):
    """Wait for the launch. Returns (fault, timed_out); with stop_on_fault, returns grace seconds
    after a pillar leaves its 85 mm circle (the round is over by rule), leaving the launch running."""
    path = directory/'pillars-gt.jsonl'
    offset, deadline, fault = 0, time.time()+timeout, None
    while proc.poll() is None:
        if time.time() > deadline:
            return fault, fault is None
        if fault is None and path.exists():
            with path.open() as f:
                f.seek(offset)
                chunk = f.read()
            complete = chunk[:chunk.rfind('\n')+1]
            offset += len(complete)
            for line in complete.splitlines():
                name = pillar_outside_circle(json.loads(line), seats)
                if name:
                    fault = dict(pillar=name, wall_time=time.time())
                    print(f'round over: {name} left its circle', flush=True)
                    if stop_on_fault:
                        deadline = min(deadline, time.time()+grace)
                    break
        time.sleep(.5)
    return fault, False


def run_launch(command, directory, seats, args):
    with (directory/'launch.log').open('w') as log:
        env = os.environ.copy()
        env['ROS_LOG_DIR'] = str(directory/'ros-log')
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=env)
        try:
            fault, timed_out = watch_for_round_fault(proc, directory, seats, args.wall_timeout,
                                                     not args.keep_running_after_fault)
        except BaseException:
            os.killpg(proc.pid, signal.SIGINT)
            proc.wait(timeout=15)
            raise
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
    return proc.returncode, fault, timed_out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--direction', choices=['cw', 'ccw'], required=True, help='start heading; the car detects it')
    parser.add_argument('--seed', type=int, default=0, help='regulation layout seed')
    parser.add_argument('--layout', choices=['regulation', 'regulation-park', 'parking'], default='regulation',
                        help='regulation-park: the layout with the parking lot (v2 parks after the laps); '
                             'parking: open field with only the parking lot; the car only parks')
    parser.add_argument('--strategy', choices=['v3', 'v2', 'current'], default='v3',
                        help='v3 (default) or v2: robotek_obstacle/v3 or v2 (obstacle_strategy_v3/v2, profile '
                             'obstacle_v3/v2.yaml); current: the original node (obstacle_sensors_v1.yaml)')
    parser.add_argument('--profile', default='',
                        help="default: the strategy's profile (obstacle_v3.yaml; obstacle_sensors_v1.yaml with "
                             '--strategy current)')
    parser.add_argument('--param', action='append', default=[], help='key=value override')
    parser.add_argument('--no-gui', action='store_true')
    parser.add_argument('--no-rviz', action='store_true')
    parser.add_argument('--spawn-progress', type=float, default=-.25)
    parser.add_argument('--wall-timeout', type=float, default=400.)
    parser.add_argument('--launch-arg', action='append', default=[], help='extra launch argument key:=value')
    parser.add_argument('--real-time-factor', type=float, help='physics real_time_factor (0 = as fast as possible)')
    parser.add_argument('--steer-p-gain', type=float, default=5.0, help='Gazebo AckermannSteering steer_p_gain')
    parser.add_argument('--keep-running-after-fault', action='store_true',
                        help='do not stop when a pillar leaves its circle')
    args = parser.parse_args()
    if any(item.startswith('honest:=') for item in args.launch_arg):
        parser.error('honest:= no longer exists: every simulation is honest (sensor noise on).')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.name):
        parser.error('name must be filename-safe')
    RUNS.mkdir(exist_ok=True)
    directory = RUNS/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+args.name)
    directory.mkdir()
    pillars, command, manifest = prepare_round(args, directory, ROOT)
    manifest['start_wall_time'] = time.time()
    write_json(directory/'manifest.json', manifest)
    print(str(directory), flush=True)
    code, fault, timed_out = run_launch(command, directory, pillars, args)
    manifest.update(stopped_on_pillar_fault=fault if fault and not args.keep_running_after_fault else None,
                    wall_timeout_reached=timed_out, end_wall_time=time.time())
    write_json(directory/'manifest.json', manifest)
    # Ground truth comes from the audit recorders; telemetry.raw.csv keeps what the strategy saw.
    merge_audit_pose(directory, keys=('x_gt', 'y_gt', 'yaw_gt', 'steer_actual', 'steer_right_actual'))
    report = summarize(directory, manifest)
    report.update(launch_wall_seconds=manifest['end_wall_time']-manifest['start_wall_time'],
                  name=args.name, directory=str(directory), direction=args.direction, launch_exit_code=code,
                  stopped_on_pillar_fault=manifest['stopped_on_pillar_fault'], wall_timeout_reached=timed_out)
    write_json(directory/'round.json', report)
    with (RUNS/'rounds.jsonl').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)   # rounds can run in parallel (tools/obstacle_gazebo_batch.py)
        f.write(json.dumps(report)+'\n')
    # One short line (the full report is round.json; tools/round_digest.py summarises it).
    judge, valid = report.get('rule_judge') or {}, report.get('validation') or {}
    print(json.dumps(dict(name=args.name, points=report.get('points_estimated'), valid=valid.get('passed'),
                          margin=valid.get('margin_class'), time=judge.get('time_from_start_sim_seconds'),
                          end=(judge.get('round_end') or {}).get('reason'), failed=valid.get('failed'))), flush=True)


if __name__ == '__main__':
    main()
