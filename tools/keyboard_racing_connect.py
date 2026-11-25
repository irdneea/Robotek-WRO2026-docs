#!/usr/bin/env python3
"""Drive the real car like a racing game from a computer: a small window, arrows / W A S D held and combined.

    python3 tools/keyboard_racing_connect.py [--speed 0.2] [--steer 15] [--pi-ip 192.168.8.153]

Run it from a terminal where ROS 2 Jazzy is already loaded (Linux, macOS with RoboStack, or Windows with RoboStack or
the official binaries). On the car first: ros2 launch robotek_course car.launch.py teleop:=true [motor_max_rps:=1.3]

It uses the same network as the car (Cyclone DDS, ROS_DOMAIN_ID 1, discovery in the subnet, the Pi as a static peer)
and then opens keyboard_racing.py. The computer must be on the car's Wi-Fi. On Windows, the firewall must let Python
receive UDP (allow it on private networks the first time). With several network cards, set CYCLONEDDS_URI to pick the
Wi-Fi one; on macOS this script picks it by itself.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

from robotek_env import TOOLS

DEFAULT_IP = '192.168.8.153'


def car_environment(env, pi_ip, interface=None):
    """A copy of ``env`` with the network settings that reach the car."""
    out = dict(env)
    out['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    out['ROS_DOMAIN_ID'] = env.get('REAL_CAR_DOMAIN_ID', '1')
    out['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'SUBNET'
    out.setdefault('ROS_STATIC_PEERS', pi_ip)
    if interface:
        out['CYCLONEDDS_URI'] = (f'<CycloneDDS><Domain><General><Interfaces><NetworkInterface name="{interface}" '
                                 'multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General>'
                                 '</Domain></CycloneDDS>')
    return out


def mac_interface(pi_ip):
    out = subprocess.run(['route', '-n', 'get', pi_ip], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    found = re.search(r'interface:\s*(\S+)', out.stdout)
    return found.group(1) if found else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--speed', type=float, default=0.2, help='m/s')
    parser.add_argument('--steer', type=float, default=15.0, help='degrees')
    parser.add_argument('--pi-ip', default=os.environ.get('PI_IP', DEFAULT_IP))
    options = parser.parse_args(argv)
    ros2 = shutil.which('ros2')
    if not ros2:
        print('ROS 2 is not loaded in this terminal (no ros2 command): load your Jazzy environment first.',
              file=sys.stderr)
        return 1
    interface = mac_interface(options.pi_ip) if sys.platform == 'darwin' else None
    env = car_environment(os.environ, options.pi_ip, interface)
    print(f"keyboard_racing: ROS domain {env['ROS_DOMAIN_ID']}, car {options.pi_ip}, speed {options.speed} m/s, "
          f'steering {options.steer} degrees', flush=True)
    if os.name == 'nt':
        if subprocess.run(['ping', '-n', '1', options.pi_ip], stdout=subprocess.DEVNULL).returncode:
            print(f"No reply from {options.pi_ip}: are you on the car's Wi-Fi and is the car on?", file=sys.stderr)
        subprocess.run([ros2, 'daemon', 'stop'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run([sys.executable, str(TOOLS / 'keyboard_racing.py'), str(options.speed), str(options.steer)],
                          env=env).returncode


if __name__ == '__main__':
    sys.exit(main())
