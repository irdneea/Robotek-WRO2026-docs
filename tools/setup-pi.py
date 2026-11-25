#!/usr/bin/env python3
"""Prepare a Raspberry Pi (Ubuntu 24.04, arm64) to run the strategies on the Robotek car.

    git clone <the URL of this repository> && cd <the repository folder>
    python3 tools/setup-pi.py              # installs and builds (asks for sudo when needed)
    python3 tools/setup-pi.py --check      # only checks: installs nothing and moves nothing
    python3 tools/setup-pi.py --dry-run    # shows the commands without running them
    python3 tools/setup-pi.py --skip-build # everything except the colcon build

What it does (it can be repeated: what is already done is skipped):
  1. checks the system (Ubuntu 24.04);
  2. installs ROS 2 Jazzy base, without Gazebo or RViz (install-ubuntu.py --no-gazebo), and the apt packages the car
     needs;
  3. installs the udev rules (tools/99-robotek.rules) and adds you to the groups dialout, video and gpio;
  4. builds the workspace: colcon build --symlink-install.

SAFETY: this script starts no node and moves neither the motor nor the servo. The first time you launch the car,
put it on supports with the wheels in the air. See src/robotek_hardware/README.md.
"""
import argparse
import glob
import grp
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from robotek_env import REPO, ROS_SETUP, TOOLS

GROUPS = ['dialout', 'video', 'gpio']
APT_PACKAGES = ['ros-jazzy-cv-bridge', 'ros-jazzy-robot-state-publisher', 'ros-jazzy-xacro', 'ros-jazzy-tf2-ros',
                'python3-serial', 'python3-lgpio', 'python3-opencv', 'python3-numpy', 'python3-yaml', 'v4l-utils']
BUILD = 'source "$1" && cd "$2" && colcon build --symlink-install'


def say(text):
    print(f'\033[1;34m>>>\033[0m {text}', flush=True)


def warn(text):
    print(f'\033[1;33m!!!\033[0m {text}', file=sys.stderr, flush=True)


def line(colour, tag, text):
    print(f'  \033[1;{colour}m{tag}\033[0m {text}', flush=True)


def first_existing(*patterns):
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            return path
    return None


def user_groups(user=None):
    out = subprocess.run(['id', '-nG', *([user] if user else [])], stdout=subprocess.PIPE, text=True).stdout
    return out.split()


def os_release(path='/etc/os-release'):
    try:
        text = Path(path).read_text()
    except OSError:
        return {}
    return dict(entry.split('=', 1) for entry in text.replace('"', '').splitlines() if '=' in entry)


def check():
    """Report what is missing; returns 0 when everything is there."""
    say('Check (nothing is installed or moved)')
    failed = []

    def good(text):
        line(32, 'ok  ', text)

    def bad(text):
        line(31, 'FAIL', text)
        failed.append(text)

    if os.path.isfile(ROS_SETUP):
        good('ROS 2 Jazzy')
    else:
        bad('ROS 2 Jazzy is not installed')
    if (REPO / 'install').is_dir():
        good('workspace built (install/)')
    else:
        bad('the workspace is not built: colcon build --symlink-install')
    board = first_existing('/dev/rrc_lite', '/dev/ttyACM0')
    if board:
        good(f'RRC Lite board on {board}')
    else:
        bad('RRC Lite board (USB 1a86:55d4, /dev/ttyACM0): plug it in with the data USB cable')
    lidar = first_existing('/dev/ldlidar', '/dev/ttyUSB0')
    if lidar:
        good(f'LiDAR on {lidar}')
    else:
        bad('LD19 LiDAR (USB 10c4:ea60, /dev/ttyUSB0) not found')
    usb_camera = first_existing('/dev/v4l/by-id/*-video-index0')
    if shutil.which('rpicam-vid'):
        good('rpicam-vid (Pi camera on the flex cable, camera_driver:=picam)')
    elif usb_camera:
        good(f'USB camera on {usb_camera}')
    else:
        line(33, 'info', 'no rpicam-vid and no USB camera: the Open takes the direction_fallback and the LiDAR corrects it')
    mine = user_groups()
    for group in GROUPS:
        if group in mine:
            good(f'you are in the group {group}')
        else:
            bad(f'you are not in the group {group} (sudo usermod -aG {group} $USER, then log in again)')
    if failed:
        warn('Something is missing (see above).')
        return 1
    say('Everything looks ready.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dry-run', action='store_true', help='show the commands without running them')
    parser.add_argument('--check', action='store_true', help='only check; install nothing')
    parser.add_argument('--skip-build', action='store_true', help='everything except the colcon build')
    options = parser.parse_args(argv)
    if options.check:
        return check()

    def run(*command):
        if options.dry_run:
            print('    $ ' + ' '.join(shlex.quote(str(c)) for c in command), flush=True)
        else:
            subprocess.run([str(c) for c in command], check=True)

    # 1. System
    system = os_release()
    if system.get('ID') != 'ubuntu' or system.get('VERSION_ID') != '24.04':
        warn(f"System {system.get('ID', 'unknown')} {system.get('VERSION_ID', '?')}: this is only tested on Ubuntu "
             '24.04. Continuing only with --dry-run or ROBOTEK_FORCE=1.')
        if not options.dry_run and os.environ.get('ROBOTEK_FORCE') != '1':
            print('For the simulator on a laptop use tools/install-ubuntu.py.', file=sys.stderr)
            return 1

    # 2. ROS 2 Jazzy and the apt packages
    if os.path.isfile(ROS_SETUP):
        say('ROS 2 Jazzy is already installed')
    else:
        say('Installing ROS 2 Jazzy base')
        run(sys.executable, TOOLS / 'install-ubuntu.py', '--no-gazebo')
    say('Installing the apt packages of the car')
    run('sudo', 'apt-get', 'install', '-y', *APT_PACKAGES)

    # 3. udev rules and groups
    udev = subprocess.run(['pidof', 'systemd-udevd'], stdout=subprocess.DEVNULL).returncode == 0
    if not udev and not options.dry_run:
        warn('systemd-udevd is not running (a container?): skipping the udev rules and the groups.')
    else:
        say('Installing the udev rules')
        run('sudo', 'cp', TOOLS / '99-robotek.rules', '/etc/udev/rules.d/99-robotek.rules')
        run('sudo', 'udevadm', 'control', '--reload-rules')
        run('sudo', 'udevadm', 'trigger')
        user = os.environ.get('SUDO_USER') or os.environ.get('USER') or ''
        if user in ('', 'root'):
            warn('Running as root without SUDO_USER: add the user to the groups by hand: '
                 'usermod -aG dialout,video,gpio USER')
        else:
            existing = {g.gr_name for g in grp.getgrall()}
            mine = user_groups(user)
            missing = []
            for group in GROUPS:
                if group not in existing:
                    run('sudo', 'groupadd', group)
                if group not in mine:
                    missing.append(group)
            if missing:
                say(f"Adding {user} to the groups: {','.join(missing)} (log out and in again for them to count)")
                run('sudo', 'usermod', '-aG', ','.join(missing), user)
            else:
                say(f'{user} is already in dialout, video and gpio')

    # 4. Build
    if options.skip_build:
        say('Skipping the build (--skip-build)')
    else:
        say('Building the workspace')
        if options.dry_run:
            print(f'    $ (cd {REPO} && source {ROS_SETUP} && colcon build --symlink-install)', flush=True)
        else:
            subprocess.run(['bash', '-c', BUILD, 'bash', ROS_SETUP, str(REPO)], check=True)

    if options.dry_run:
        say('End of --dry-run: nothing was executed.')
    else:
        print('''
Next steps:
  1. If you were added to new groups, log out and in again.
  2. python3 tools/setup-pi.py --check           # board, LiDAR, camera and groups
  3. With the car on supports (wheels in the air):
       python3 tools/obstacle-round.py            # Obstacle Challenge
       python3 tools/car-run.py open              # Open Challenge
     The board LEDs turn green when the sensors give data; the board button is Start (a second press stops).''')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        sys.exit(f'A command failed with code {error.returncode}: {error.cmd}')
