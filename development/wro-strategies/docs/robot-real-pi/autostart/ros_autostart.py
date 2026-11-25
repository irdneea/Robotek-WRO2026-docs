#!/usr/bin/env python3
"""Historical record, translated from the shell script that was on the Pi (disabled on 9 Oct 2026; see README.md).

It started the old stack at boot in the mode written in ~/.config/wro_mode. The current car does not use it.
"""
import os
from pathlib import Path
import sys

HOME = Path.home()


def mode():
    try:
        return ''.join((HOME / '.config/wro_mode').read_text().split())
    except OSError:
        return 'open'


def main():
    os.environ['ROS_DOMAIN_ID'] = '1'       # the same ROS domain as the previous configuration
    selected = mode()
    if selected == 'open':
        script = str(HOME / 'Documents/Testv1/open/run_open.sh')       # lived only on the Pi; not in this repository
        os.execv('/bin/bash', ['/bin/bash', script])
    if selected == 'obstacle':
        load = 'source "$1" && source "$2" && exec ros2 launch rrc_lite_driver wro.launch.py'
        os.execv('/bin/bash', ['/bin/bash', '-c', load, 'bash', '/opt/ros/jazzy/setup.bash',
                               str(HOME / 'Projects/WRO-Strategies/install/setup.bash')])
    print(f'Invalid mode: {selected} (use open or obstacle)', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
