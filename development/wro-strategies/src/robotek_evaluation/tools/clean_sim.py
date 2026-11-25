#!/usr/bin/env python3
"""Stop every Robotek simulation and strategy process, including nodes left behind when a launch is killed.

    python3 src/robotek_evaluation/tools/clean_sim.py        # run it before every launch
"""
import os
import re
import signal
import subprocess
import sys
import time

PATTERNS = [
    r'ros2 launch',
    r'(^|[ /])parameter_bridge([ ]|$)',
    r'(^|[ /])open_strategy(_v5)?([ ]|$)',
    r'(^|[ /])obstacle_strategy(_v2)?([ ]|$)',
    r'(^|[ /])(obstacle_audit_recorder|audit_pose_recorder|sim_actuator_model)([ ]|$)',
    r'(^|[ /])robot_state_publisher([ ]|$)',
    r'gz sim',
    r'gz-sim',
    r'(^|[ /])rviz2([ ]|$)',
]


def processes():
    out = subprocess.run(['ps', '-eo', 'pid=,ppid=,args='], stdout=subprocess.PIPE, text=True, check=True).stdout
    rows = (line.split(None, 2) for line in out.splitlines())
    return [(int(r[0]), int(r[1]), r[2]) for r in rows if len(r) == 3]


def matching(table):
    """The processes to stop. This script and its callers never are: a terminal command line can contain
    "ros2 launch" or "gz sim" and would otherwise be stopped by mistake."""
    parents = {pid: ppid for pid, ppid, _ in table}
    skip, pid = set(), os.getpid()
    while pid > 1 and pid not in skip:
        skip.add(pid)
        pid = parents.get(pid, 0)
    return [(pid, args) for pid, _, args in table
            if pid not in skip and any(re.search(pattern, args) for pattern in PATTERNS)]


def send(sig):
    for pid, _ in matching(processes()):
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass


def main():
    send(signal.SIGTERM)
    time.sleep(2)
    send(signal.SIGKILL)      # for whatever ignored the first signal (the Gazebo server and window, for example)
    time.sleep(1)
    left = matching(processes())
    if not left:
        print('clean: no sim/strategy processes running')
        return 0
    print('still running:')
    for pid, args in left:
        print(pid, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
