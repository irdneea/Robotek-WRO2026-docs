#!/usr/bin/env python3
"""RViz on the Mac to watch the real car (Pi) over Wi-Fi, with the RoboStack environment.

    python3 tools/macos_rviz_real.py                                        # robot_obstacle.rviz
    python3 tools/macos_rviz_real.py docs/robot-real-pi/robot_camera.rviz   # only the camera (compressed)

Default network of the Mac and the Pi (README, "Red entre el Mac y el Pi"): Cyclone DDS, domain 1 and discovery in
the subnet, the same on both sides. If the Pi has no Cyclone yet: REAL_CAR_RMW=rmw_fastrtps_cpp (and the Pi with
Fast DDS, which is what it ships with). It closes any RViz that is already open.
"""
import os
import subprocess
import sys
import time

import car_network
import devenv
import macos_env


def main(argv):
    os.chdir(devenv.ROOT)
    config = argv[0] if argv else 'docs/robot-real-pi/robot_obstacle.rviz'
    env, pi_ip, iface = car_network.environment(macos_env.environment())
    print(f"RViz: RMW={env['RMW_IMPLEMENTATION']} domain={env['ROS_DOMAIN_ID']} "
          f"discovery={env['ROS_AUTOMATIC_DISCOVERY_RANGE']} Pi={pi_ip} {'interface=' + iface if iface else ''}",
          flush=True)
    subprocess.run(['ros2', 'daemon', 'stop'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-x', 'rviz2'])
    time.sleep(1)
    os.execvpe('rviz2', ['rviz2', '-d', config], env)


if __name__ == '__main__':
    main(sys.argv[1:])
