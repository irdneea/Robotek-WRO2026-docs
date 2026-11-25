#!/usr/bin/env python3
"""Open standard set (12 rounds) of the v5 strategy with a quality gate.

    tools/open_suite_quiet.py <tag>

It waits for a quiet machine (load <= 8) and repeats, up to 3 times, a round whose node fell behind the simulation:
control ticks more than 0.2 s apart, or LiDAR stamps drifting from /clock by more than 0.1 s anywhere in the run.
Rounds with clean=0 stay as attempts.
"""
import csv
import gzip
import json
import os
import subprocess
import sys

import devenv

FIELDS = ['square100', 'square180', 'rect100x180', 'rect180x100', 'shift140', 'east140x100']
YAW = {'ccw': '0.0', 'cw': '3.141592653589793'}
WORLDS = 'docs/open-challenge-runs/field-size-driver/worlds'


def arguments(tag, field, direction):
    return [f'std12-{tag}-{field}-{direction}', '--strategy', 'v5',
            '--params-file', 'src/robotek_open/config/open_v5.yaml', '--world', f'{WORLDS}/{field}.sdf',
            '--direction', direction, '--controller-direction', 'auto', '--spawn-x', '0.0', '--spawn-y', '-1.15',
            '--spawn-yaw', YAW[direction], '--ackermann-velocity-limit', '4.0', '--ackermann-steer-p-gain', '20',
            '--launch-arg', 'real_car:=true', '--no-gui', '--real-time-factor', '2']


def is_clean(path):
    try:
        with open(path / 'telemetry.csv') as f:
            times = [float(r['sim_time']) for r in csv.DictReader(f)]
        times = [t for t in times if t > 1]
        steps = [d for d in (b - a for a, b in zip(times, times[1:])) if d < 1]
        with gzip.open(path / 'telemetry.csv.scans.jsonl.gz', 'rt') as f:
            lag = [r['stamp'] - r['sim_time'] for r in map(json.loads, f)]
        return bool(steps) and max(steps) <= 0.2 and max(lag[10:]) < 0.1 and min(lag[10:]) > -0.1
    except Exception:
        return False


def summary(path, clean, attempt):
    r = devenv.read_round(path)
    v = r.get('validation') or {}
    return '%-46s pts=%-3s t=%-7s valid=%-5s %-12s clean=%d attempt=%d %s' % (
        path.name[17:], r.get('points_estimated'), devenv.sim_time(r), v.get('passed'), v.get('margin_class'),
        clean, attempt, ','.join(v.get('failed', [])))


def main(argv):
    if not argv:
        print('usage: open_suite_quiet.py <tag>', file=sys.stderr)
        return 2
    tag = argv[0]
    os.chdir(devenv.ROOT)
    for field in FIELDS:
        for direction in YAW:
            for attempt in (1, 2, 3):
                devenv.wait_until_quiet(8)
                devenv.run_tool(devenv.EVALUATION_TOOLS / 'run_open_round.py', *arguments(tag, field, direction),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                path = devenv.newest('open-challenge-runs', f'-std12-{tag}-{field}-{direction}')
                clean = bool(path) and is_clean(path)
                try:
                    print(summary(path, clean, attempt), flush=True)
                except Exception as error:
                    print(f'{field}-{direction}: no round record ({type(error).__name__}) attempt={attempt}',
                          flush=True)
                if clean:
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
