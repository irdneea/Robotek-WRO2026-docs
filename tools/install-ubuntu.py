#!/usr/bin/env python3
"""Install ROS 2 Jazzy, Gazebo Harmonic (through ros_gz) and the tools of the project on Ubuntu 24.04 (also WSL2).

    python3 tools/install-ubuntu.py
    python3 tools/install-ubuntu.py --no-gazebo

It follows https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html and asks for sudo.
--no-gazebo (the Raspberry Pi of the real car, used by setup-pi.py): installs ros-jazzy-ros-base instead of the
desktop (no RViz, no Gazebo, no ros_gz). Run as root (a container) it does not need sudo.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from robotek_env import ROS_SETUP

RELEASES = 'https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest'
SOURCE_LINE = 'source /opt/ros/jazzy/setup.bash'
COMMON = ['ros-jazzy-rmw-cyclonedds-cpp', 'python3-pytest']


def package_url(version, codename):
    return ('https://github.com/ros-infrastructure/ros-apt-source/releases/download/'
            f'{version}/ros2-apt-source_{version}.{codename}_all.deb')


def ros_packages(gazebo):
    base = ['ros-jazzy-desktop', 'ros-jazzy-ros-gz'] if gazebo else ['ros-jazzy-ros-base']
    return ['ros-dev-tools', *base, *COMMON]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--no-gazebo', action='store_true', help='ROS base only (the Raspberry Pi of the car)')
    gazebo = not parser.parse_args(argv).no_gazebo
    sudo = [] if os.geteuid() == 0 else ['sudo']

    def run(*command):
        subprocess.run([*sudo, *command], check=True)

    def step(text):
        print(f'>>> {text}', flush=True)

    step('[1/5] UTF-8 locale')
    run('apt', 'update')
    run('apt', 'install', '-y', 'locales')
    run('locale-gen', 'en_US', 'en_US.UTF-8')
    run('update-locale', 'LC_ALL=en_US.UTF-8', 'LANG=en_US.UTF-8')
    os.environ['LANG'] = 'en_US.UTF-8'

    step('[2/5] Ubuntu universe repository')
    run('apt', 'install', '-y', 'software-properties-common', 'curl', 'git')
    run('add-apt-repository', 'universe', '-y')

    step('[3/5] ROS 2 apt source')
    run('apt', 'update')
    with urllib.request.urlopen(RELEASES, timeout=30) as reply:
        version = json.load(reply)['tag_name']
    release = dict(entry.split('=', 1) for entry in
                   Path('/etc/os-release').read_text().replace('"', '').splitlines() if '=' in entry)
    deb = '/tmp/ros2-apt-source.deb'
    urllib.request.urlretrieve(package_url(version, release.get('UBUNTU_CODENAME') or release['VERSION_CODENAME']), deb)
    run('dpkg', '-i', deb)

    step('[4/5] ROS 2 Jazzy desktop (RViz), Gazebo bridge, colcon and pytest (a few GB, take a coffee)' if gazebo
         else '[4/5] ROS 2 Jazzy base (no RViz, no Gazebo), colcon and pytest')
    run('apt', 'update')
    run('apt', 'install', '-y', *ros_packages(gazebo))

    step('[5/5] ROS 2 in every new terminal')
    bashrc = Path.home() / '.bashrc'
    text = bashrc.read_text() if bashrc.exists() else ''
    if SOURCE_LINE not in text.splitlines():
        bashrc.write_text(text + ('' if not text or text.endswith('\n') else '\n') + SOURCE_LINE + '\n')

    step('Check:')
    check = 'source "$1" && echo "ROS_DISTRO=$ROS_DISTRO"' + (' && gz sim --versions' if gazebo else '')
    subprocess.run(['bash', '-c', check, 'bash', ROS_SETUP], check=True)
    step('Done. Open a new terminal.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        sys.exit(f'A command failed with code {error.returncode}: {error.cmd}')
