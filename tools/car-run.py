#!/usr/bin/env python3
"""Launch a strategy on the car by hand, with everything it needs.

It stops the autostart and any leftover nodes (car-clean.py), sets the network the computer of the team sees
(Cyclone DDS, domain 1, subnet discovery) and runs car.launch.py.

    python3 tools/car-run.py open                      # Open v5 with the car defaults (robotek_open/config/car_picam.yaml)
    python3 tools/car-run.py obstacle                  # Obstacle v3 (robotek_obstacle_v3/config/car_picam.yaml)
    python3 tools/car-run.py obstacle motor_rps_per_mps:=8.0   # motor turns per m/s (robot.yaml: 7.0, 1:1 gears)
    python3 tools/car-run.py open cruise_speed:=0.8    # any car.launch argument after the name
    python3 tools/car-run.py open camera_always:=true  # the camera on for the whole round, to watch or record it in RViz
    VERBOSE=1 python3 tools/car-run.py open            # every log line (default: only the summary below)

Shown by default: ready / running, Start and Stop, the strategy's state changes with the time since Start, each
section with its time, each sign seen and passed (side, OK / WRONG SIDE) and the ROUND line (Obstacle), lap times,
the final time, the parking verdict, where the round is recorded (both strategies write
~/runs/<date>-<time>-open-v5/ or -obstacle-v3/: telemetry.csv, events.jsonl, the scans), and anything that looks
wrong (errors, a dead node, board reboots, low battery). The whole output is still in ~/.ros/log/<date>/launch.log.

The car's defaults (picam camera, rear sensor only for the Obstacle, motor cap, speeds) come from car.launch and the
strategy's car_picam.yaml: nothing else to type.
"""
import os
import re
import signal
import subprocess
import sys

from robotek_env import ros_environment, tool

STRATEGIES = {'open': ['strategy:=robotek_open', 'executable:=open_v5'],
              'obstacle': ['strategy:=robotek_obstacle_v3']}

SUMMARY = re.compile(
    r'READY|RUNNING|: Start\.|: Stop|state [A-Z_]+|(straight|corner) [0-9]+ \(lap|sign (seen|colour|passed)|ROUND '
    r'|LAP [0-9]|DONE:|park verdict|park pulse|park finish pulses|STEER FAULT|CAMERA LOST|camera back|rpicam'
    r'|Telemetry:|Park: mode|CRASH|ERROR|Traceback|has died|rebooted|Board reset|Battery [0-9.]+ V <')


def command(argv):
    """The ``ros2 launch`` command for the arguments of this script, or None if the first one is not a challenge."""
    if not argv or argv[0] not in STRATEGIES:
        return None
    return ['ros2', 'launch', 'robotek_course', 'car.launch.py', *STRATEGIES[argv[0]], *argv[1:]]


def main(argv):
    launch = command(argv)
    if launch is None:
        print('usage: python3 tools/car-run.py open|obstacle [car.launch args...]', file=sys.stderr)
        return 2
    tool('car-autostart.py', 'stop', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if tool('car-clean.py').returncode:
        return 1
    env = ros_environment()
    sys.stdout.flush()
    if os.environ.get('VERBOSE') == '1':
        os.execvpe(launch[0], launch, env)
    process = subprocess.Popen(launch, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, errors='replace', bufsize=1)
    # Ctrl-C reaches the launch too (same terminal). This script keeps reading, so that the shutdown lines are shown
    # and it ends when the launch ends. Set after Popen, so that the launch does not inherit it.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    for line in process.stdout:
        if SUMMARY.search(line):
            print(line, end='', flush=True)
    return process.wait()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
