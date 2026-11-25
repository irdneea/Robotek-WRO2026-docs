#!/usr/bin/env python3
"""Ablation of Obstacle parameters in Gazebo (4 rounds per piece), for docs/obstacle-reimpl-v2.md.

    tools/obstacle_param_ablation.py [tag] [only-this-piece]

Only parameters declared in ObstacleConfig can be changed here. Fixed values (ClassVar: plan_loc_gain,
plan_side_cost, plan_view_gain, plan_steps, plan_beam, recover, ...) need a temporary patch in a branch, never in
main (docs/obstacle-reimpl-plan.md, phase 1). One line per round. Run it with no other batch running: quiet machine,
no window.
"""
import os
import subprocess
import sys

import devenv

PROFILE = 'src/robotek_obstacle/config/obstacle_sensors_v1.yaml'
PIECES = [
    ('base', []),
    ('marginsup', ['plan_wall_margin=0.05', 'plan_pillar_margin=0.06', 'plan_soft=0.07']),
    ('speed035', ['plan_speed=0.35']),
]
ROUNDS = [(0, 'ccw'), (1, 'cw'), (2, 'ccw'), (3, 'cw')]


def arguments(tag, name, params, seed, direction):
    changes = [item for p in params for item in ('--param', p)]
    return ['--name', f'{tag}-{name}-reg{seed}-{direction}', '--seed', str(seed), '--direction', direction,
            '--profile', PROFILE, '--strategy', 'current', '--steer-p-gain', '20', '--launch-arg', 'real_car:=true',
            '--no-gui', '--no-rviz', '--real-time-factor', '1', '--wall-timeout', '320', *changes]


def summary(path, name):
    r = devenv.read_round(path)
    v = r.get('validation') or {}
    margin = '%.1fcm' % (v['min_clearance_m'] * 100) if v.get('min_clearance_m') else '-'
    return '%-10s %-20s pts=%-3s t=%-7s valid=%-5s %-9s m=%-6s %s' % (
        name, path.name.split('-reg', 1)[-1], r.get('points_estimated'), devenv.sim_time(r), v.get('passed'),
        v.get('margin_class'), margin, ','.join(v.get('failed', [])))


def main(argv):
    tag = argv[0] if argv else 'abl'
    only = argv[1] if len(argv) > 1 else ''
    os.chdir(devenv.ROOT)
    limit = int(os.environ.get('QUIET_LOAD') or 6)
    for name, params in PIECES:
        if only and name != only:
            continue
        for seed, direction in ROUNDS:
            devenv.wait_until_quiet(limit)
            devenv.run_tool(devenv.EVALUATION_TOOLS / 'run_obstacle_round.py',
                            *arguments(tag, name, params, seed, direction),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            path = devenv.newest('obstacle-challenge-runs', f'-{tag}-{name}-reg{seed}-{direction}')
            try:
                print(summary(path, name), flush=True)
            except Exception as error:
                print(f'{name} reg{seed}-{direction}: no round record ({type(error).__name__})', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
