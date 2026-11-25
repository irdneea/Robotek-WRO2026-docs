#!/usr/bin/env python3
"""Record the real car's run from the Mac (Wi-Fi) into a rosbag, with the RoboStack environment.

    python3 tools/car_bag_mac.py [name]            # Ctrl-C to stop; ~/rondas-coche/bags/<date-time>-<name>/
    CAMERA=1 python3 tools/car_bag_mac.py          # also the strategy's debug image (heavier over Wi-Fi)

Topics: the LiDAR (raw and adapted), IMU, rear distance sensor, the GPIO button and Start, the commands
(/cmd_vel_raw, motor, servo, estop), the strategy's state, pose and signs, battery, /tf_static and /rosout
(the strategy's log lines, the lot exit's included). Network as macos_rviz_real.py: the Pi must use the same
(car-autostart does; a manual launch needs RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET). The bags are telemetry: they stay on the Mac, not in git.
"""
import datetime
import os
from pathlib import Path
import subprocess
import sys

import car_network
import devenv
import macos_env

TOPICS = ['/scan', '/robotek/scan', '/robotek/imu', '/rrc/imu_raw', '/robotek/rear_range_mm', '/robotek/rear_range',
          '/robotek/gpio_button', '/start', '/robotek/stop', '/robotek/estop', '/cmd_vel_raw', '/rrc/set_motor',
          '/rrc/acker_servo/set_state', '/robotek/state', '/obstacle/pose', '/obstacle/signs', '/rrc/battery',
          '/tf_static', '/rosout']


def topics(camera):
    return TOPICS + (['/obstacle/debug_image/compressed'] if camera else [])


def main(argv):
    os.chdir(devenv.ROOT)
    name = argv[0] if argv else 'car'
    env, pi_ip, iface = car_network.environment(macos_env.environment())
    out = Path.home() / 'rondas-coche/bags' / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + name)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"bag: {out} (RMW={env['RMW_IMPLEMENTATION']} domain={env['ROS_DOMAIN_ID']} Pi={pi_ip} "
          f"{'interface=' + iface if iface else ''})", flush=True)
    # The ROS daemon keeps the previous RMW and domain.
    subprocess.run(['ros2', 'daemon', 'stop'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    command = ['ros2', 'bag', 'record', '-o', str(out), *topics(env.get('CAMERA') == '1')]
    os.execvpe('ros2', command, env)


if __name__ == '__main__':
    main(sys.argv[1:])
