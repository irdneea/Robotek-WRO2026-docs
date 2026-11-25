"""Shared helpers of the scripts in this folder (not run on its own)."""
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / 'tools'
ROS_SETUP = os.environ.get('ROBOTEK_ROS_SETUP', '/opt/ros/jazzy/setup.bash')

# The network that the computer of the team sees (RViz, keyboard): Cyclone DDS, domain 1, discovery in the subnet.
CAR_NETWORK = {'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp', 'ROS_DOMAIN_ID': '1',
               'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET'}


def ros_environment():
    """The environment after loading ROS 2 and this workspace, with the car's network settings.

    ROS only offers shell files for this, so they are loaded in a shell that then prints its environment.
    """
    load = 'source "$1" >/dev/null && source "$2" >/dev/null && env -0'
    result = subprocess.run(['bash', '-c', load, 'bash', ROS_SETUP, str(REPO / 'install' / 'setup.bash')],
                            stdout=subprocess.PIPE)
    if result.returncode:
        sys.exit('Could not load ROS 2 and the workspace. Is it built? (colcon build --symlink-install)')
    entries = result.stdout.decode().split('\0')
    env = dict(entry.split('=', 1) for entry in entries if '=' in entry)
    env.update(CAR_NETWORK)
    return env


def tool(name, *args, **kwargs):
    """Run another script of this folder with the same Python."""
    return subprocess.run([sys.executable, str(TOOLS / name), *args], **kwargs)
