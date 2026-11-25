#!/usr/bin/env python3
"""One Open v5 test on the car WITHOUT the button, recording everything to analyse it afterwards.

    python3 tools/open-debug-run.py [extra launch arguments]      # e.g. motor_max_rps:=6 start_delay:=8

It stops the autostart service (car-autostart.py) and every leftover car node (car-clean.py) so that the board and the
LiDAR are free, starts a rosbag and launches car.launch.py with the Open v5, button:=false (the car starts by itself
after start_delay, 12 s by default; the board button then STOPS it) and debug:=true. Ctrl-C ends the launch and closes
the bag. Everything goes to ~/runs/<date>-<time>-open-debug/:

    launch.log   the terminal output (debug: states, direction, corners, laps)
    bag/         commands (/cmd_vel_raw), servo pulses and motor speed sent to the board, LiDAR, IMU,
                 battery, mission state, start/stop and steering arrow (5 s chunks)
    cpu.log      top every second (8 busiest processes)
    telemetry    link to the strategy's telemetry.csv (~/runs/<date>-<time>-open-v5/)

The autostart is NOT turned back on: python3 tools/car-autostart.py start (or the next boot does it).
"""
import datetime
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading

from robotek_env import ros_environment, tool

# Not the detector JPEG nor /open/turn: the strategy only builds them while someone subscribes, and in its single thread
# that work slowed the control loop (33-39 Hz instead of 50, 4 Nov 2026). RViz can still show them; DEBUG_BAG_ALL=1
# adds them to the bag.
TOPICS = ['/cmd_vel_raw', '/rrc/acker_servo/set_state', '/rrc/set_motor', '/robotek/scan', '/robotek/imu',
          '/rrc/imu_raw', '/rrc/battery', '/robotek/state', '/start', '/robotek/stop', '/robotek/estop', '/open/steer',
          '/joint_states', '/tf_static', '/rosout']
EXTRA_TOPICS = ['/camera/direction_debug/compressed', '/open/turn']
LAUNCH = ['ros2', 'launch', 'robotek_course', 'car.launch.py', 'strategy:=robotek_open', 'executable:=open_v5',
          'button:=false', 'debug:=true']


def keep_cpu_lines(lines, out, limit=8):
    """From the output of top, keep each header and the ``limit`` busiest processes after it."""
    shown = 0
    for line in lines:
        if line.startswith('top -'):
            shown = 0
        elif not re.match(r' *[0-9]+ ', line) or shown >= limit:
            continue
        else:
            shown += 1
        out.write(line)
        out.flush()


def stop(process, sig=signal.SIGINT):
    """Ask a process to end, and insist with SIGTERM if it ignores the first signal."""
    if process.poll() is None:
        process.send_signal(sig)
        try:
            process.wait(5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait()


def main(argv):
    out = Path.home() / 'runs' / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-open-debug')
    out.mkdir(parents=True, exist_ok=True)
    tool('car-autostart.py', 'stop', stderr=subprocess.DEVNULL)
    # Every car node of an earlier launch out first (they would run next to the new ones: 4 Nov 2026).
    tool('car-clean.py')
    env = ros_environment()
    topics = TOPICS + (EXTRA_TOPICS if os.environ.get('DEBUG_BAG_ALL') == '1' else [])
    print(f'Recording to {out}. The car starts by itself after start_delay (12 s); the board button stops it; '
          'Ctrl-C ends.', flush=True)
    with open(out / 'bag.log', 'wb') as bag_log, open(out / 'cpu.log', 'w') as cpu_log:
        # Each recorder has its own session: Ctrl-C only reaches the launch, and they are stopped afterwards.
        bag = subprocess.Popen(['ros2', 'bag', 'record', '--max-bag-duration', '5', '-o', str(out / 'bag'), *topics],
                               env=env, stdout=bag_log, stderr=subprocess.STDOUT, start_new_session=True)
        top = subprocess.Popen(['top', '-b', '-d', '1', '-o', '%CPU', '-w', '160'], stdout=subprocess.PIPE, text=True,
                               errors='replace', start_new_session=True)
        cpu = threading.Thread(target=keep_cpu_lines, args=(top.stdout, cpu_log), daemon=True)
        cpu.start()
        code = 1
        try:
            launch = subprocess.Popen(LAUNCH + argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, errors='replace', bufsize=1)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            with open(out / 'launch.log', 'w') as launch_log:
                for line in launch.stdout:
                    print(line, end='', flush=True)
                    launch_log.write(line)
                    launch_log.flush()
            code = launch.wait()
        finally:
            stop(top, signal.SIGTERM)
            cpu.join(2)
            stop(bag)
            runs = sorted((Path.home() / 'runs').glob('*-open-v5'), key=lambda p: p.stat().st_mtime)
            if runs and not (out / 'telemetry').exists():
                (out / 'telemetry').symlink_to(runs[-1])
            os.sync()
            print(f'Saved in {out}')
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
