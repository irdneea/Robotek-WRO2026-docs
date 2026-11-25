#!/usr/bin/env python3
"""Obstacle standard set (seeds 0-4 x ccw/cw = 10 rounds) with a quality gate.

    tools/obstacle_suite_quiet.py <tag> [profile.yaml] [extra runner arguments]

It waits for a quiet machine (load <= 4 by default; QUIET_LOAD changes it) and repeats, up to 3 times, a round whose
node fell behind the simulation: control ticks more than 0.2 s apart, or LiDAR stamps drifting from /clock by more
than 0.1 s anywhere in the run. Rounds with clean=0 stay in the ledger as attempts. The limit is 4, not 8 as in the
Open: each Obstacle round is about 80 s of simulation and Gazebo alone adds about 4 to the load, so a start at 8
already produced lagged rounds (22 Oct 2026).
"""
import csv
import gzip
import json
import os
import subprocess
import sys

import devenv

PROFILE = 'src/robotek_obstacle/config/obstacle_v3.yaml'   # v3; obstacle_sensors_v1.yaml needs --strategy current


def split_arguments(argv):
    """(tag, profile, extra): the second argument is the profile only if it is a .yaml file."""
    tag, rest = argv[0], argv[1:]
    if rest and rest[0].rsplit('.', 1)[-1] == 'yaml':
        return tag, rest[0], rest[1:]
    return tag, PROFILE, rest


def arguments(tag, profile, seed, direction, extra):
    return ['--name', f'{tag}-reg{seed}-{direction}', '--seed', str(seed), '--direction', direction,
            '--profile', profile, '--steer-p-gain', '20', '--launch-arg', 'real_car:=true',
            '--no-gui', '--no-rviz', '--real-time-factor', '2', '--wall-timeout', '320', *extra]


def is_clean(path):
    """True if the strategy kept up with the simulation during the whole round."""
    try:
        with open(path / 'telemetry.csv') as f:
            times = [float(r['sim_time']) for r in csv.DictReader(f)]
        steps = [b - a for a, b in zip(times, times[1:]) if 0 < b - a < 1]
        with gzip.open(path / 'scans.jsonl.gz', 'rt') as f:
            lag = [r['stamp'] - r['sim_time'] for r in map(json.loads, f)]
        return bool(steps) and max(steps) <= 0.2 and max(lag[10:]) < 0.1 and min(lag[10:]) > -0.1
    except Exception:          # a missing or damaged record is not a clean round
        return False


def summary(path, clean, attempt):
    try:
        r = devenv.read_round(path)
    except Exception:
        return '%-46s (no round.json) clean=%d attempt=%d' % (path.name if path else '-', clean, attempt)
    v = r.get('validation') or {}
    return '%-46s pts=%-3s t=%-7s valid=%-5s %-9s clean=%d attempt=%d %s' % (
        path.name, r.get('points_estimated'), devenv.sim_time(r), v.get('passed'), v.get('margin_class'),
        clean, attempt, ','.join(v.get('failed', [])))


def main(argv):
    if not argv:
        print('usage: obstacle_suite_quiet.py <tag> [profile.yaml] [extra runner args]', file=sys.stderr)
        return 2
    tag, profile, extra = split_arguments(argv)
    os.chdir(devenv.ROOT)
    limit = int(os.environ.get('QUIET_LOAD') or 4)
    for seed in range(5):
        for direction in ('ccw', 'cw'):
            for attempt in (1, 2, 3):
                devenv.wait_until_quiet(limit)
                devenv.run_tool(devenv.EVALUATION_TOOLS / 'run_obstacle_round.py',
                                *arguments(tag, profile, seed, direction, extra),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                path = devenv.newest('obstacle-challenge-runs', f'-{tag}-reg{seed}-{direction}')
                clean = bool(path) and is_clean(path)
                print(summary(path, clean, attempt), flush=True)
                if clean:
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
