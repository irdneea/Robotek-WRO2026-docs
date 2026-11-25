#!/usr/bin/env python3
"""On the Pi: use Cyclone DDS, domain 1 and discovery in the subnet by default (the same as the Mac).

First, by hand and with sudo:  sudo apt install ros-jazzy-rmw-cyclonedds-cpp
Then, from the computer:       ssh <user>@<car-address> python3 - < tools/pi_use_cyclone.py
or on the Pi itself:           python3 tools/pi_use_cyclone.py

Nothing changes if Cyclone is not installed (an RMW that does not exist breaks every ROS command). It can be run
again: a marked block is added to ~/.bashrc only once. Nodes that are already running keep the RMW they started
with: launch them again.
"""
import os
from pathlib import Path
import sys

LIBRARY = os.environ.get('ROBOTEK_CYCLONE_LIB', '/opt/ros/jazzy/lib/librmw_cyclonedds_cpp.so')
MARK = '# >>> robotek dds >>>'
BLOCK = f'''
{MARK}
# Same RMW, domain and discovery as the Mac (README: "Red entre el Mac y el Pi")
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
# <<< robotek dds <<<
'''


def main():
    if not os.path.exists(LIBRARY):
        print('Cyclone DDS is not installed: first run  sudo apt install ros-jazzy-rmw-cyclonedds-cpp', file=sys.stderr)
        return 1
    bashrc = Path.home() / '.bashrc'
    text = bashrc.read_text() if bashrc.exists() else ''
    if MARK in text:
        print('~/.bashrc already has the DDS block; nothing changes.')
    else:
        bashrc.write_text(text + BLOCK)
        print('Added to ~/.bashrc: Cyclone DDS, ROS_DOMAIN_ID=1, discovery SUBNET.')
    print("Check it in a NEW terminal:  ros2 doctor --report | grep -i 'middleware name'")
    return 0


if __name__ == '__main__':
    sys.exit(main())
