#!/usr/bin/env python3
"""Stop the whole ROS 2 stack of the old configuration of the car (translated from its shell script; see README.md).

The current car uses tools/car-clean.py of the main repository instead.
"""
import getpass
import subprocess
import time

# Only the processes of the car's stack.
PATTERN = (r'ros2 (launch|run)|ros2-daemon|local_launch[.]py|open_controller[.]py|tb6612fng_driver[.]py'
           r'|ldlidar_stl_ros2_node|rrc_lite_driver/.*/rrc_driver')


def main():
    # The service holds the launch and all its nodes: stopping it sends SIGTERM to the whole group, so that the motor
    # and the servo are turned off by the controller's safe shutdown.
    subprocess.run(['systemctl', '--user', 'stop', 'ros_autostart.service'], stderr=subprocess.DEVNULL)
    user = getpass.getuser()
    subprocess.run(['pkill', '-TERM', '-u', user, '-f', PATTERN], stderr=subprocess.DEVNULL)
    time.sleep(1)
    subprocess.run(['pkill', '-KILL', '-u', user, '-f', PATTERN], stderr=subprocess.DEVNULL)
    print('ROS 2 stack of the car stopped.')


if __name__ == '__main__':
    main()
