#!/usr/bin/env python3
"""Open Challenge standard validation set: 6 fields x 2 directions, the same start for every profile.

    open_standard_suite.py <tag> <profile.yaml> [extra run_gui_experiment arguments...]

It runs Open v5, the only strategy. Prefer tools/open_suite_quiet.py (it waits for a quiet machine). Rounds are named
std12-<tag>-<field>-<direction>; use the same tag for one profile and servo pair.
"""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
import devenv  # noqa: E402

FIELDS = ['square100', 'square180', 'rect100x180', 'rect180x100', 'shift140', 'east140x100']
YAW = {'ccw': '0.0', 'cw': '3.141592653589793'}


def arguments(tag, profile, field, direction, extra):
    world = devenv.ROOT / f'docs/open-challenge-runs/field-size-driver/worlds/{field}.sdf'
    return [f'std12-{tag}-{field}-{direction}', '--params-file', profile, '--world', str(world),
            '--direction', direction, '--controller-direction', 'auto', '--spawn-x', '0.0', '--spawn-y', '-1.15',
            '--spawn-yaw', YAW[direction], '--ackermann-velocity-limit', '4.0', *extra]


def summary(path):
    r = devenv.read_round(path)
    v = r.get('validation') or {}
    return '%-46s pts=%-3s t=%-7s valid=%-5s %-12s %s' % (
        path.name[17:], r.get('points_estimated'), devenv.sim_time(r), v.get('passed'), v.get('margin_class'),
        ','.join(v.get('failed', [])))


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    tag, profile, extra = argv[0], argv[1], argv[2:]
    for field in FIELDS:
        for direction in YAW:
            devenv.run_tool(HERE / 'run_open_round.py', *arguments(tag, profile, field, direction, extra),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            path = devenv.newest('open-challenge-runs', f'-std12-{tag}-{field}-{direction}')
            try:
                print(summary(path), flush=True)
            except Exception as error:
                print(f'{field}-{direction}: no round record ({type(error).__name__})', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
