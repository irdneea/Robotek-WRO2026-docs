#!/usr/bin/env python3
"""Small, progressive changes of the start position of the Open; every attempt uses the recorded runner.

    tools/run_open_start_suite.py <tag> <profile.yaml> [stage 1|2|3] [field]
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import devenv

STAGES = {
    '1': [('xp10', '0.10', '-1.15'), ('xm10', '-0.10', '-1.15')],
    '2': [('yp05', '0.0', '-1.10'), ('ym05', '0.0', '-1.20')],
    '3': [('xp25', '0.25', '-1.15'), ('xm25', '-0.25', '-1.15'), ('yp15', '0.0', '-1.0'), ('ym15', '0.0', '-1.30')],
}
YAW = {'ccw': '0.0', 'cw': '3.141592653589793'}


def arguments(name, profile, world, direction, x, y):
    return [name, '--params-file', profile, '--world', world, '--direction', direction,
            '--controller-direction', 'auto', '--spawn-x', x, '--spawn-y', y, '--spawn-yaw', YAW[direction],
            '--ackermann-velocity-limit', '4.0', '--ackermann-steer-p-gain', '20',
            '--launch-arg', 'real_car:=true', '--no-gui', '--real-time-factor', '0']


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    tag, profile = argv[0], argv[1]
    stage = argv[2] if len(argv) > 2 else '1'
    field = argv[3] if len(argv) > 3 else 'square100'
    os.chdir(devenv.ROOT)
    world = f'docs/open-challenge-runs/field-size-driver/worlds/{field}.sdf'
    if not Path(world).is_file():
        print(f'No such field: {world}', file=sys.stderr)
        return 1
    if stage not in STAGES:
        print('Stage must be 1, 2 or 3', file=sys.stderr)
        return 2
    field_tag = 'sq100' if field == 'square100' else field
    for label, x, y in STAGES[stage]:
        for direction in YAW:
            name = f'realcar-starts-{tag}-{field_tag}-{label}-{direction}'
            log_path = Path(tempfile.gettempdir()) / f'{name}.log'
            with open(log_path, 'w') as log:
                code = devenv.run_tool(devenv.EVALUATION_TOOLS / 'run_open_round.py',
                                       *arguments(name, profile, world, direction, x, y),
                                       stdout=log, stderr=subprocess.STDOUT).returncode
            if code:
                print(f'The runner failed with code {code}; see {log_path}', file=sys.stderr)
                return code
            path = devenv.newest('open-challenge-runs', '-' + name)
            r = devenv.read_round(path)
            judge, validation = r.get('rule_judge') or {}, r.get('validation') or {}
            print(path.name, 'points=', r['points_estimated'], 'sim=', judge.get('time_from_start_sim_seconds'),
                  'valid=', validation.get('passed'), 'failed=', validation.get('failed'), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
