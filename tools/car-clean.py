#!/usr/bin/env python3
"""Stop every car node still running from an earlier launch, then set the motors to 0.

    python3 tools/car-clean.py         # before each run (car-autostart.py and car-run.py call it)

A launch stopped from a script or over ssh can leave its children running (a background job ignores Ctrl-C). On
4 Nov 2026 such leftovers ran a second strategy and a second board driver next to the new launch, and three
round_reporter at 22-30 % CPU each slowed the strategy to 4-14 Hz: the car drove straight into a wall.
It stops: the nodes of this workspace (install/*/lib), the ROS helpers car.launch.py starts (robot_state_publisher,
static_transform_publisher, usb_cam), ros2 launch / ros2 bag record of a car run, the debug recorder and an rpicam-vid
left by a killed pi_camera_publisher (12 Nov 2026: it kept the camera busy, 'failed to acquire camera').
SIGINT first (nodes close cleanly), then SIGTERM, then SIGKILL for whatever is still there.
"""
import os
import re
import signal
import subprocess
import sys
import time

from robotek_env import REPO

BOARD = '/dev/rrc_lite'


def pattern(repo):
    """Regular expression that matches the command line of every process this script stops."""
    return '|'.join([
        re.escape(str(repo)) + r'/install/[^ ]*/lib/',
        r'opt/ros/jazzy/lib/robot_state_publisher/',
        r'opt/ros/jazzy/lib/tf2_ros/static_transform_publisher',
        r'usb_cam_node',
        r'ros2 launch robotek_course',
        r'ros2 bag record',
        r'open-debug-run\.py',
        r'top -b -d 1 -o %CPU',
        r'ros2 topic echo --once /start',
        r'journalctl -k -f -n 0',
        r'rpicam-vid -t 0 -n --codec yuv420'])


def select(table, regex):
    """PIDs to stop. ``table`` is a list of (pid, ppid, command line); ``regex`` the pattern above.

    This script and its callers are never selected: a caller whose own command line matches the pattern would stop
    itself (it happened on 8 Nov 2026).
    """
    parents = {pid: ppid for pid, ppid, _ in table}
    skip, pid = set(), os.getpid()
    while pid > 1 and pid not in skip:
        skip.add(pid)
        pid = parents.get(pid, 0)
    return [pid for pid, _, args in table if pid not in skip and re.search(regex, args)]


def processes():
    out = subprocess.run(['ps', '-eo', 'pid=,ppid=,args='], stdout=subprocess.PIPE, text=True, check=True).stdout
    table = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            table.append((int(parts[0]), int(parts[1]), parts[2]))
    return table


def stop_processes(regex):
    def running():
        return select(processes(), regex)

    found = running()
    if not found:
        print('car-clean: no car nodes running.')
        return
    print(f'car-clean: stopping {len(found)} processes: {" ".join(map(str, found))}')
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGKILL):
        left = running()
        if not left:
            break
        for pid in left:
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
        for _ in range(10):
            if not running():
                break
            time.sleep(0.5)
    left = running()
    if left:
        print(f'car-clean: still running after SIGKILL: {" ".join(map(str, left))}', file=sys.stderr)


ZERO_MOTORS = '''
import sys, time
sys.path.insert(0, sys.argv[1] + '/src/rrc_lite_driver/rrc_lite_driver')
from rrc_lite_driver_sdk.board import Board
board = Board(device=sys.argv[2])
for _ in range(10):
    board.set_motor_speed([[1, 0.0], [2, 0.0], [3, 0.0], [4, 0.0]])
    time.sleep(0.05)
'''


def zero_motors():
    """Motors to 0 straight on the board (nothing else holds the port now). Skipped when there is no board."""
    if not os.path.exists(BOARD):
        return
    try:
        result = subprocess.run([sys.executable, '-c', ZERO_MOTORS, str(REPO), BOARD],
                                stderr=subprocess.DEVNULL, timeout=5)
    except subprocess.TimeoutExpired:
        return
    if result.returncode == 0:
        print('car-clean: motors at 0.')


def main():
    sys.stdout.reconfigure(line_buffering=True)
    stop_processes(pattern(REPO))
    zero_motors()
    return 0


if __name__ == '__main__':
    sys.exit(main())
