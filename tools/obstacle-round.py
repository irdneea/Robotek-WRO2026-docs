#!/usr/bin/env python3
"""The Obstacle round as the coach ran it last (12 Nov 2026, 1:1 gears).

Start inside the lot, leave it with the hard-coded pulses, three laps, then the partial park and the hard-coded pulses
that left the car parallel in the lot (car_picam_park_round.yaml: team field lot 0.31 / 0.3675 m). Any extra
car.launch argument goes after it, for example:

    python3 tools/obstacle-round.py                        # exactly the coach's command
    python3 tools/obstacle-round.py direction:=cw park_fixed_sense:=2

The results of this command are in the README, chapter 10.
"""
import os
import sys

from robotek_env import REPO, TOOLS

PROFILE = REPO / 'install/robotek_obstacle_v3/share/robotek_obstacle_v3/config/car_picam_park_round.yaml'


def arguments(extra):
    """The arguments passed to car-run.py."""
    return ['obstacle', 'start_lot:=true', f'strategy_params:={PROFILE}', 'motor_rps_per_mps:=8.0',
            'motor_min_rps:=2', 'recover_back:=0.3', 'lot_exit_speed:=0.2',
            'lot_exit_steps:=L+0.25 R-0.3 L+0.25 R-0.3 L+0.25 R-0.3 C-0.2', *extra]


if __name__ == '__main__':
    os.execv(sys.executable, [sys.executable, str(TOOLS / 'car-run.py'), *arguments(sys.argv[1:])])
