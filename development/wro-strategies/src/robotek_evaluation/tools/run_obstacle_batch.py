#!/usr/bin/env python3
"""Run several recorded Obstacle rounds (regulation layouts) one after another.

    [STRATEGY=v3|v2|current] run_obstacle_batch.py <name-prefix> <profile.yaml> "<seeds>" "<directions>" [runner args]
"""
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def arguments(prefix, profile, seed, direction, strategy, extra):
    return ['--name', f'{prefix}-reg{seed}-{direction}', '--seed', seed, '--direction', direction,
            '--profile', profile, '--strategy', strategy, '--wall-timeout', '320', *extra]


def main(argv):
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    prefix, profile, seeds, directions, extra = argv[0], argv[1], argv[2].split(), argv[3].split(), argv[4:]
    strategy = os.environ.get('STRATEGY') or 'v3'
    for direction in directions:
        for seed in seeds:
            command = [sys.executable, str(HERE / 'run_obstacle_round.py'),
                       *arguments(prefix, profile, seed, direction, strategy, extra)]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    errors='replace')
            for line in result.stdout.splitlines():
                if line.startswith('{'):
                    print(line[:400], flush=True)      # the runner's one-line JSON result
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
