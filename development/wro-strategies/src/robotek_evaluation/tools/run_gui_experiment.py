#!/usr/bin/env python3
"""Run one Open experiment and preserve logs, sensors and per-round measurements."""

import argparse
import json
import time
from pathlib import Path

from robotek_evaluation.open_experiment_analysis import merge_audit_pose, summarize
from robotek_evaluation.open_experiment_process import LaunchError, execute_experiment
from robotek_evaluation.open_experiment_setup import prepare_experiment
from robotek_open.open_profile import load_parameters
from robotek_evaluation.open_round_report import save_round_report

# Kept for existing callers that load this command as a module.
__all__ = ('load_parameters', 'summarize', 'merge_audit_pose', 'main')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--strategy', choices=['v5'], default='v5', help='Open strategy: v5, the only one (v4 and older were removed)')
    parser.add_argument('--param', action='append', default=[], help='key=value ROS parameter')
    parser.add_argument('--params-file', type=Path, help='Saved strategy profile YAML')
    parser.add_argument('--world', type=Path, help='Open field SDF override')
    parser.add_argument('--direction', choices=['cw', 'ccw'], default='ccw')
    parser.add_argument('--controller-direction', choices=['auto', 'cw', 'ccw'])
    parser.add_argument('--spawn-x', type=float, default=0.0)
    parser.add_argument('--spawn-y', type=float, default=-1.0)
    parser.add_argument('--spawn-yaw', type=float)
    parser.add_argument('--rviz', action='store_true')
    parser.add_argument('--no-gui', action='store_true', help='headless Gazebo (camera still renders)')
    parser.add_argument('--honest', action='store_true',
                        help='no effect, kept for old commands: every run is honest (sensor noise on)')
    parser.add_argument('--real-time-factor', type=float, help='physics real_time_factor (0 = as fast as possible)')
    parser.add_argument('--ackermann-steer-p-gain', type=float, default=1.0)
    parser.add_argument('--ackermann-velocity-limit', type=float, default=1.0)
    parser.add_argument('--timeout', type=float, default=240)
    parser.add_argument('--max-recoveries', type=int, default=3)
    parser.add_argument('--launch-arg', action='append', default=[],
                        help='extra launch argument key:=value (e.g. actuator_model:=true)')
    args = parser.parse_args()
    if any(item.startswith('honest:=') for item in args.launch_arg):
        parser.error('honest:= no longer exists: every simulation is honest (sensor noise on).')
    return args


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[3]
    directory, command = prepare_experiment(args, root)
    print('RESULTS_DIR=' + str(directory), flush=True)
    try:
        execution = execute_experiment(command, root, directory, args)
    except LaunchError as error:
        result = {'completed': False, 'abort_reason': str(error), 'exit_code': None}
    else:
        merged = merge_audit_pose(directory)
        try:
            result = summarize(directory)
        except (ValueError, KeyError, OSError) as error:
            result = {'completed': False, 'reason': 'Summary failed: ' + str(error)}
        started = execution.pop('started_monotonic')
        result.update(honest=True, audit_pose_merged=merged,
                      launch_wall_seconds=time.monotonic() - started, **execution)
    result['round'] = save_round_report(directory, result)
    (directory / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    # One short line (summary.json and round.json keep everything; tools/round_digest.py summarises).
    report = result.get('round') if isinstance(result.get('round'), dict) else {}
    judge, valid = report.get('rule_judge') or {}, report.get('validation') or {}
    print(json.dumps(dict(run=directory.name, completed=result.get('completed'),
                          points=report.get('points_estimated'), valid=valid.get('passed'),
                          margin=valid.get('margin_class'), time=judge.get('time_from_start_sim_seconds'),
                          failed=valid.get('failed'), reason=result.get('abort_reason') or result.get('reason'))),
          flush=True)


if __name__ == '__main__':
    main()
