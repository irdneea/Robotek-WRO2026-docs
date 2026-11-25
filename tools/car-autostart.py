#!/usr/bin/env python3
"""Start the car's launch by itself every time the Raspberry Pi boots (systemd user service, no sudo).

    python3 tools/car-autostart.py on [launch arguments]   # e.g. on motor_max_rps:=6 (default: the Open v5)
    python3 tools/car-autostart.py off                     # stop it and do not start it at boot any more
    python3 tools/car-autostart.py start | stop            # now, without changing the boot setting (stop also
                                                           # cleans leftover car nodes: tools/car-clean.py)
    python3 tools/car-autostart.py status | log [lines]    # is it running, its output (journalctl)

It always waits for the board button: button:=false is refused here, because the car would drive off
12 s after every boot. The arguments are saved in ~/.config/robotek/autostart-args; run "on" again to
change them. It runs the code of this folder (git pull + colcon build as usual; it uses the
build at the next start). It needs lingering for the user (loginctl show-user $USER | grep Linger=yes) so that it
starts without anyone logging in; the Pi of the team already has it.
"""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time

from robotek_env import REPO, TOOLS, ros_environment, tool

UNIT = 'robotek-car.service'
UNIT_FILE = Path.home() / '.config/systemd/user' / UNIT
ARGS_FILE = Path.home() / '.config/robotek/autostart-args'
DEFAULT_ARGS = ['strategy:=robotek_open', 'executable:=open_v5']   # camera, motor cap and params: car.launch defaults
BAG_TOPICS = ['/cmd_vel_raw', '/rrc/acker_servo/set_state', '/rrc/set_motor', '/rrc/reset', '/robotek/scan',
              '/robotek/imu', '/rrc/imu_raw', '/rrc/battery', '/robotek/state', '/start', '/robotek/stop',
              '/robotek/estop', '/open/steer', '/tf_static', '/rosout']


def launch_arguments(argv):
    """The car.launch arguments that "on" saves; raises ValueError for button:=false."""
    args = list(argv) or list(DEFAULT_ARGS)
    if any(a in ('button:=false', 'button:=False') for a in args):
        raise ValueError('button:=false is not allowed at boot: the car would start driving by itself.')
    if not any(a.startswith('strategy:=') for a in args):
        args = DEFAULT_ARGS + args
    return args


def unit_text(python, script):
    return f'''[Unit]
Description=robotek car launch at boot (car.launch.py, waits for the board button)

[Service]
Type=simple
ExecStart={python} "{script}" run
# No restart: a car that relaunches by itself in the middle of a round is worse than one that stops.
Restart=no
KillSignal=SIGINT
TimeoutStopSec=15

[Install]
WantedBy=default.target
'''


def systemctl(*args):
    return subprocess.run(['systemctl', '--user', *args]).returncode


def wait_for_network():
    """Wait up to 60 s for an IPv4 address: Cyclone DDS picks its network interface when it starts, and without the
    Wi-Fi the computer of the team (RViz, keyboard) would not see the car."""
    for _ in range(60):
        try:
            out = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
        except OSError:
            out = ''
        if any(c.isdigit() for c in out):
            return
        time.sleep(1)


def record(folder):
    """Wait for Start, then record a light rosbag in 5 s chunks (not while the car waits)."""
    waited = subprocess.run(['ros2', 'topic', 'echo', '--once', '/start', 'std_msgs/msg/Bool'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if waited.returncode:
        return waited.returncode
    log = os.open(os.path.join(folder, 'bag.log'), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    os.dup2(log, 1)
    os.dup2(log, 2)
    os.execvp('ros2', ['ros2', 'bag', 'record', '--max-bag-duration', '5', '-o', os.path.join(folder, 'bag'),
                       *BAG_TOPICS])


def run():
    """What the service runs at boot."""
    wait_for_network()
    env = ros_environment()
    args = ARGS_FILE.read_text().split()
    # Nothing of an earlier launch may run next to this one (two strategies, two board drivers: 4 Nov 2026).
    tool('car-clean.py')
    # Every round leaves its evidence in ~/runs/<date>-<time>-autostart/ (4 Nov 2026: a round that failed in its last
    # corner left nothing to explain it): launch.log (this output), kernel.log (USB drops of the board, "disabled by
    # hub (EMI?)") and bag/, the rosbag.
    out = Path.home() / 'runs' / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-autostart')
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'kernel.log', 'wb') as kernel:
        subprocess.Popen(['journalctl', '-k', '-f', '-n', '0'], stdout=kernel, stderr=subprocess.STDOUT)
    subprocess.Popen([sys.executable, str(TOOLS / 'car-autostart.py'), 'record', str(out)], env=env)
    tee = subprocess.Popen(['tee', str(out / 'launch.log')], stdin=subprocess.PIPE)
    sys.stdout.flush()
    os.dup2(tee.stdin.fileno(), 1)
    os.dup2(tee.stdin.fileno(), 2)
    print(f'robotek-car: ros2 launch robotek_course car.launch.py {" ".join(args)} (recording to {out})', flush=True)
    os.execvpe('ros2', ['ros2', 'launch', 'robotek_course', 'car.launch.py', *args], env)


def main(argv):
    action, rest = (argv[0], argv[1:]) if argv else ('', [])
    if action == 'on':
        try:
            args = launch_arguments(rest)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        UNIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ARGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        ARGS_FILE.write_text(' '.join(args) + '\n')
        UNIT_FILE.write_text(unit_text('/usr/bin/python3', TOOLS / 'car-autostart.py'))
        if systemctl('daemon-reload') or systemctl('enable', UNIT):
            return 1
        print(f'At every boot: ros2 launch robotek_course car.launch.py {" ".join(args)}')
        print('Start it now with: python3 tools/car-autostart.py start')
    elif action == 'off':
        subprocess.run(['systemctl', '--user', 'disable', '--now', UNIT], stderr=subprocess.DEVNULL)
        print('Autostart off.')
    elif action in ('start', 'status'):
        return systemctl(action, UNIT)
    elif action == 'stop':
        # The launch can leave children behind: clean them too (tools/car-clean.py).
        code = systemctl('stop', UNIT)
        return code or tool('car-clean.py').returncode
    elif action == 'log':
        lines = int(rest[0]) if rest else 60
        out = subprocess.run(['journalctl', '--user', '-u', UNIT, '-b', '--no-pager'],
                             stdout=subprocess.PIPE, text=True, errors='replace')
        print('\n'.join(out.stdout.splitlines()[-lines:]))
        return out.returncode
    elif action == 'run':
        run()
    elif action == 'record' and rest:
        return record(rest[0])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
