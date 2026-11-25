#!/usr/bin/env python3
"""The environment to build and run the simulation on macOS (RoboStack Jazzy). Details: docs/simulacion-macos.md.

    python3 tools/macos_env.py -- colcon build              # run one command inside it
    python3 tools/macos_env.py                              # open a shell inside it
    python3 tools/macos_env.py --env /path/to/env -- ...    # another RoboStack env (default ~/Projects/WRO/.mamba/jazzy)

A program cannot change the terminal that started it, so instead of loading the environment into your shell this
script starts the command (or a new shell) inside it. The other scripts of the workspace use ``environment()``.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

from devenv import ROOT, sourced

# ROS and Gazebo variables inherited from Homebrew or an old shell. A colcon build run with
# COLCON_PREFIX_PATH=/opt/homebrew/opt/ros2-jazzy chains that prefix into install/setup.sh, and `ros2 launch` then
# starts Homebrew's `create` and `parameter_bridge`, which abort.
CLEARED = ['COLCON_PREFIX_PATH', 'ROS_PACKAGE_PATH', 'PKG_CONFIG_PATH', 'CMAKE_MODULE_PATH', 'PYTHONPATH',
           'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'GZ_CONFIG_PATH', 'GZ_GUI_PLUGIN_PATH', 'GZ_SIM_RESOURCE_PATH',
           'GZ_SIM_SYSTEM_PLUGIN_PATH', 'GZ_SIM_PHYSICS_ENGINE_PATH', 'GZ_RENDERING_PLUGIN_PATH',
           'GZ_RENDERING_RESOURCE_PATH', 'GZ_SIM_RENDER_ENGINE_PATH']


def robostack(path=None):
    return Path(path or os.environ.get('ROBOSTACK_ENV') or Path.home() / 'Projects/WRO/.mamba/jazzy')


def colcon_defaults(env_path):
    """The car's LiDAR driver only builds on Linux, and rrc_lite_msgs needs RoboStack's Python (with NumPy)."""
    return ('build:\n  packages-skip: [ldlidar_stl_ros2]\n'
            f'  cmake-args: ["-DPython3_EXECUTABLE={env_path}/bin/python"]\n')


def base_environment(env_path, start):
    env = {k: v for k, v in start.items() if k not in CLEARED}
    env['ROBOSTACK_ENV'] = str(env_path)
    paths = [p for p in env.get('PATH', '').split(':') if '/opt/homebrew/opt/ros2-' not in p]
    env['PATH'] = ':'.join([f'{env_path}/bin', *paths])
    # `micromamba activate` leaves AMENT_PREFIX_PATH empty: set it by hand.
    env['AMENT_PREFIX_PATH'] = env['CMAKE_PREFIX_PATH'] = str(env_path)
    # The conda gz-rendering has a broken OGRE plugin path: without this the Metal render system is not found and
    # `gz sim` crashes when the camera or the LiDAR start.
    env['OGRE2_RESOURCE_PATH'] = f'{env_path}/lib/OGRE-Next'
    env['OGRE_RESOURCE_PATH'] = f'{env_path}/lib/OGRE'
    # Fast DDS on macOS drops most 640x480 camera frames (UDP datagrams of at most 9216 bytes).
    env['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    # Only this machine: do not talk to the car or other computers of the network.
    env['ROS_DOMAIN_ID'] = env.get('ROS_DOMAIN_ID') or '42'
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    return env


def environment(path=None):
    env_path = robostack(path)
    if not os.access(env_path / 'bin/ros2', os.X_OK):
        sys.exit(f'macos_env: no RoboStack env with ros2 at {env_path}')
    env = base_environment(env_path, os.environ)
    defaults = Path(tempfile.gettempdir()) / 'robotek-colcon-defaults-macos.yaml'
    defaults.write_text(colcon_defaults(env_path))
    env['COLCON_DEFAULTS_FILE'] = str(defaults)
    chained = ROOT / 'install/setup.sh'
    if chained.is_file() and '/opt/homebrew' in chained.read_text():
        print('macos_env: install/setup.sh chains Homebrew ROS; rebuild inside this environment', file=sys.stderr)
    if (ROOT / 'install/setup.bash').is_file():
        env = sourced([ROOT / 'install/setup.bash'], env=env)
    else:
        print('macos_env: no install/ yet; run: colcon build --packages-ignore robotek_hardware', file=sys.stderr)
    for tool in ('ros2', 'gz', 'colcon'):
        found = shutil.which(tool, path=env['PATH'])
        if not (found or '').startswith(str(env_path) + '/'):
            print(f'macos_env: {tool} is not from {env_path}: {found}', file=sys.stderr)
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--env', help='path of the RoboStack environment')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    options = parser.parse_args(argv)
    command = options.command[1:] if options.command[:1] == ['--'] else options.command
    command = command or [os.environ.get('SHELL', 'bash')]
    env = environment(options.env)
    os.execvpe(command[0], command, env)


if __name__ == '__main__':
    main()
