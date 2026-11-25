"""Launch supervision and audit-based stopping for a recorded Open attempt."""

import csv
import json
import math
import os
import re
import selectors
import signal
import subprocess
import time

from .rule_judge import mat_section


def tail_rows(path, size=4096):
    """Last complete CSV rows of a growing file (header read separately)."""
    try:
        with path.open('rb') as stream:
            header = next(csv.reader([stream.readline().decode()]))
            stream.seek(0, 2)
            end = stream.tell()
            stream.seek(max(0, end - size))
            data = stream.read().decode(errors='replace')
    except OSError:
        return []
    # Drop the first (cut) line and a last line that is still being written.
    lines = data.splitlines()[1:] if data.endswith('\n') else data.splitlines()[1:-1]
    rows = []
    # csv, not split(','): turn_trigger is quoted and has commas inside, and a plain split
    # dropped every row after a corner-triggered turn (no 180 s cut, 9 Oct 2026).
    for values in csv.reader(lines):
        if len(values) == len(header):
            rows.append(dict(zip(header, values)))
    return rows


class RoundWatch:
    """Stop a round that can no longer score: rule time limit or no section progress."""

    def __init__(self, directory, limit=180.0, stall=30.0):
        self.directory, self.limit, self.stall = directory, limit, stall
        self.start = None
        self.section = None
        self.section_since = None

    def check(self):
        if self.start is None:
            events = self.directory / 'events.jsonl'
            if events.exists():
                for line in events.read_text().splitlines():
                    event = json.loads(line)
                    if event.get('event') == 'start':
                        self.start = float(event['sim_time'])
            if self.start is None:
                return None
        rows = tail_rows(self.directory / 'telemetry.csv')
        if not rows:
            return None
        last = rows[-1]
        now = float(last['sim_time'])
        if last.get('state') == 'DONE':
            return None
        if now - self.start >= self.limit:
            return 'round_time_limit_180s'
        pose = tail_rows(self.directory / 'audit_pose.csv') or rows
        try:
            x, y = float(pose[-1]['x_gt']), float(pose[-1]['y_gt'])
        except (KeyError, ValueError):
            return None
        if not (math.isfinite(x) and math.isfinite(y)):
            return None
        section = mat_section(x, y)
        if section != self.section:
            self.section, self.section_since = section, now
        elif now - self.section_since >= self.stall:
            return 'no_section_progress_%ds' % self.stall
        return None


class LaunchError(OSError):
    """The launch process could not be started."""


def execute_experiment(command, root, directory, args):
    env = os.environ.copy()
    env['ROS_LOG_DIR'] = str(directory / 'ros-log')
    try:
        process = subprocess.Popen(
            command, cwd=root, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
    except OSError as error:
        raise LaunchError(str(error)) from error
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    started = time.monotonic()
    buffer = b''
    last_state = None
    laps = 0
    timeout = False
    recovery_entries = 0
    abort_reason = None
    watch = RoundWatch(directory)
    last_watch = 0.0
    with (directory / 'launch.log').open('wb') as log:
        while selector.get_map():
            if time.monotonic() - last_watch > 2.0 and abort_reason is None:
                last_watch = time.monotonic()
                reason = watch.check()
                if reason:
                    abort_reason = 'Round stopped by runner: ' + reason
                    print(abort_reason, flush=True)
                    os.killpg(process.pid, signal.SIGINT)
            if time.monotonic() - started > args.timeout and not timeout:
                timeout = True
                print('Experiment timeout; requesting launch shutdown.', flush=True)
                os.killpg(process.pid, signal.SIGINT)
            if timeout and time.monotonic() - started > args.timeout + 20:
                os.killpg(process.pid, signal.SIGKILL)
            for key, _ in selector.select(timeout=1):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                log.write(chunk)
                log.flush()
                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()
                for raw in lines:
                    line = re.sub(r'\x1b\[[0-9;]*m', '', raw.decode(errors='replace'))
                    match = re.search(
                        r'\[(DETECT_DIRECTION|DIRECTION_FAULT|FOLLOW|TURN|ALIGN_EXIT|'
                        r'FINISH|DONE|RECOVER)\]'
                        r'.*turns=(\d+)', line)
                    if match:
                        state, turns = match.group(1), int(match.group(2))
                        if state == 'RECOVER' and last_state != state:
                            recovery_entries += 1
                            if recovery_entries >= args.max_recoveries and abort_reason is None:
                                abort_reason = 'Repeated recovery; inspect ground truth/sensors'
                                print(abort_reason, flush=True)
                                os.killpg(process.pid, signal.SIGINT)
                        if state != last_state or turns // 4 > laps:
                            print(line, flush=True)
                        last_state, laps = state, turns // 4
                    elif 'ERROR' in line or 'mission complete' in line:
                        print(line, flush=True)
    process.wait()
    selector.close()
    process.stdout.close()
    return dict(exit_code=process.returncode, timeout=timeout,
                started_monotonic=started,
                abort_reason=abort_reason)
