#!/usr/bin/env python3
"""Look for an encoder (or any wheel/servo feedback) in what the car publishes, while the robot runs.

Runs on the Pi next to the car's stack (``bash tools/car-run.sh obstacle ...``), reads only, and writes to
``~/runs/<date>-encoder-probe/``:

* ``topics.json``  every topic seen: type, publishing nodes, message count, rate, first message and, for each numeric
  field, first / last / min / max value, how many times it changed and whether it only grows (a counter);
* ``signals.csv``  10 Hz: battery mV, gyro z, the servo command (us) and the motor command (rps), so a battery dip can be
  lined up with a steering fault afterwards (the rounds of 16 nov 2026 did not record the voltage);
* ``servo.csv``    only with ``--poll-servo``: the board's answer to ``pwm_servo/get_state`` against the last servo command;
* ``report.md``    the candidates (topics or fields that look like an encoder) and the verdict on the servo read.

Safety, from the driver's code (``pwm_servo_read_and_unpack``): the read waits on a queue with no timeout while the board
answers; if it never does, the driver's service thread blocks for good and the motor/servo commands may stop. So the
servo read is OFF by default, runs at 1 Hz at most, and a call that does not come back in ``--timeout`` s switches the
polling off for the rest of the run and says so. Use it with the wheels in the air first.

    python3 tools/encoder_probe.py --seconds 120                  # passive only (nothing is sent to the board)
    python3 tools/encoder_probe.py --seconds 120 --poll-servo 1   # also read PWM channel 1 (the team's J4)
"""
import argparse
import csv
import json
import math
import os
import re
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rosidl_runtime_py import message_to_ordereddict
from rosidl_runtime_py.utilities import get_message

SKIP_TYPES = {'sensor_msgs/msg/Image', 'sensor_msgs/msg/CompressedImage', 'sensor_msgs/msg/PointCloud2',
              'sensor_msgs/msg/LaserScan'}          # heavy, and nobody's encoder
LOOKS_LIKE = re.compile(r'encod|tick|tps|rps|wheel|odom|joint|motor|speed|veloc|counter|travel|dist', re.I)


class Leaf:
    """Statistics of one numeric field."""

    def __init__(self, value):
        self.first = self.last = self.lo = self.hi = value
        self.changes = 0
        self.up = self.down = 0

    def add(self, value):
        if value != self.last:
            self.changes += 1
            if value > self.last:
                self.up += 1
            else:
                self.down += 1
        self.last = value
        self.lo, self.hi = min(self.lo, value), max(self.hi, value)

    def as_dict(self):
        counter = self.changes >= 5 and (self.down == 0 or self.up == 0)
        return {'first': self.first, 'last': self.last, 'min': self.lo, 'max': self.hi, 'changes': self.changes,
                'only_grows_or_only_falls': counter}


def numeric_leaves(value, prefix=''):
    """(path, number) of every number in a message turned into dicts and lists (lists capped at 8 items)."""
    if isinstance(value, bool):
        yield prefix, float(value)
    elif isinstance(value, (int, float)):
        if math.isfinite(value):
            yield prefix, float(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from numeric_leaves(item, f'{prefix}.{key}' if prefix else key)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(list(value)[:8]):
            yield from numeric_leaves(item, f'{prefix}[{index}]')


class Probe(Node):
    def __init__(self, args):
        super().__init__('encoder_probe')
        self.args = args
        self.t0 = time.time()
        self.subs = {}                  # topic -> subscription
        self.stats = {}                 # topic -> dict
        self.battery = self.gyro_z = self.servo_cmd = self.motor_cmd = None
        self.out = os.path.expanduser(args.out)
        os.makedirs(self.out, exist_ok=True)
        self.signals = csv.writer(open(os.path.join(self.out, 'signals.csv'), 'w', newline='', buffering=1))
        self.signals.writerow(['t', 'battery_mV', 'gyro_z', 'servo_cmd_us', 'motor_cmd_rps'])
        self.servo_file = self.servo = self.client = None
        self.frame_stats_last = None
        self.frame_stats_file = open(os.path.join(self.out, 'frame_stats.jsonl'), 'w', buffering=1)
        self.poll_ok = False
        self.polls = []
        if args.poll_servo:
            from rrc_lite_msgs.srv import GetPWMServoState
            self.client = self.create_client(GetPWMServoState, args.service)
            self.servo_file = open(os.path.join(self.out, 'servo.csv'), 'w', newline='', buffering=1)
            self.servo = csv.writer(self.servo_file)
            self.servo.writerow(['t', 'servo_cmd_us', 'read_position', 'latency_s', 'status'])
            self.poll_ok = True
            self.create_timer(1.0 / max(args.poll_hz, 0.1), self.poll)
        self.create_timer(2.0, self.discover)
        self.create_timer(0.1, self.sample)
        self.get_logger().info(f'encoder probe: {args.seconds:.0f} s, servo read {"ON" if args.poll_servo else "off"}, '
                               f'writing to {self.out}')

    # ---------------------------------------------------------------- topics
    def discover(self):
        for topic, types in self.get_topic_names_and_types():
            if topic in self.subs or topic.startswith('/rosout') or topic.startswith('/parameter_events'):
                continue
            name = types[0]
            if name in SKIP_TYPES:
                self.stats[topic] = {'type': name, 'skipped': 'heavy type, not subscribed'}
                self.subs[topic] = None
                continue
            try:
                msg_type = get_message(name)
            except (AttributeError, ModuleNotFoundError, ValueError):
                self.stats[topic] = {'type': name, 'skipped': 'message type not importable here'}
                self.subs[topic] = None
                continue
            qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.stats[topic] = {'type': name, 'count': 0, 'leaves': {}, 'first': None, 't_first': None, 't_last': None}
            self.subs[topic] = self.create_subscription(msg_type, topic, lambda m, tp=topic: self.on_msg(tp, m), qos)

    def on_msg(self, topic, msg):
        now = time.time() - self.t0
        stat = self.stats[topic]
        stat['count'] += 1
        stat['t_first'] = stat['t_first'] if stat['t_first'] is not None else now
        stat['t_last'] = now
        data = message_to_ordereddict(msg)
        if stat['first'] is None:
            stat['first'] = json.loads(json.dumps(data, default=str))[:1] if isinstance(data, list) else \
                json.loads(json.dumps(data, default=str))
        if topic.endswith('/frame_stats'):      # the driver's count of every frame the board sent (see rrc_driver.py)
            self.frame_stats_last = json.loads(msg.data)
            self.frame_stats_file.write(msg.data + chr(10))
        for path, value in numeric_leaves(data):
            leaf = stat['leaves'].get(path)
            if leaf is None:
                stat['leaves'][path] = Leaf(value)
            else:
                leaf.add(value)
        # The few signals worth lining up with a steering fault.
        if topic.endswith('/battery') and hasattr(msg, 'data'):
            self.battery = msg.data
        elif topic.endswith('/imu_raw') and hasattr(msg, 'angular_velocity'):
            self.gyro_z = msg.angular_velocity.z
        elif topic.endswith('/acker_servo/set_state') and hasattr(msg, 'position'):
            self.servo_cmd = msg.position
        elif topic.endswith('/set_motor') and hasattr(msg, 'data') and msg.data:
            self.motor_cmd = msg.data[0].rps

    def sample(self):
        self.signals.writerow([round(time.time() - self.t0, 2), self.battery, self.gyro_z, self.servo_cmd, self.motor_cmd])

    # ----------------------------------------------------------- servo read
    def poll(self):
        if not self.poll_ok:
            return
        if not self.client.service_is_ready():
            self.servo.writerow([round(time.time() - self.t0, 2), self.servo_cmd, '', '', 'service not ready'])
            return
        from rrc_lite_msgs.msg import GetPWMServoCmd
        from rrc_lite_msgs.srv import GetPWMServoState
        request = GetPWMServoState.Request()
        cmd = GetPWMServoCmd()
        cmd.id, cmd.get_position, cmd.get_offset = self.args.channel, 1, 0
        request.cmd = [cmd]
        started = time.time()
        future = self.client.call_async(request)
        future.add_done_callback(lambda f, s=started, c=self.servo_cmd: self.polled(f, s, c))
        self.polls.append((started, future))

    def polled(self, future, started, commanded):
        latency = time.time() - started
        position = ''
        try:
            states = future.result().state
            position = states[0].position[0] if states and states[0].position else ''
        except Exception as error:      # noqa: BLE001: whatever the service raised goes to the CSV
            position = f'error {error}'
        self.servo.writerow([round(started - self.t0, 2), commanded, position, round(latency, 3), 'ok'])
        self.servo_file.flush()

    def check_polls(self):
        """A read that has not come back after --timeout s: stop polling (the driver may be blocked)."""
        now = time.time()
        for started, future in self.polls:
            if not future.done() and now - started > self.args.timeout and self.poll_ok:
                self.poll_ok = False
                self.servo.writerow([round(started - self.t0, 2), self.servo_cmd, '', '', 'NO ANSWER: polling stopped'])
                self.get_logger().error(f'servo read unanswered for {now - started:.1f} s: polling OFF. The driver may be '
                                        'blocked: check that the car still obeys before going on.')
        self.polls = [(s, f) for s, f in self.polls if not f.done()]

    # ---------------------------------------------------------------- report
    def finish(self):
        elapsed = time.time() - self.t0
        topics, candidates = {}, []
        for topic, stat in sorted(self.stats.items()):
            if 'skipped' in stat:
                topics[topic] = stat
                continue
            publishers = [i.node_name for i in self.get_publishers_info_by_topic(topic)]
            leaves = {p: leaf.as_dict() for p, leaf in stat['leaves'].items()}
            topics[topic] = {'type': stat['type'], 'publishers': publishers, 'count': stat['count'],
                             'rate_hz': round(stat['count'] / max(elapsed, 1e-6), 2), 'first_message': stat['first'],
                             'numeric_fields': leaves}
            by_name = bool(LOOKS_LIKE.search(topic))
            counters = [p for p, d in leaves.items() if d['only_grows_or_only_falls']]
            if stat['count'] and (by_name or counters):
                candidates.append((topic, stat['type'], publishers, stat['count'], by_name, counters))
        json.dump(topics, open(os.path.join(self.out, 'topics.json'), 'w'), indent=1, default=str)
        lines = [f'# Encoder probe, {elapsed:.0f} s', '',
                 f'{len(topics)} topics seen; {sum(1 for t in topics.values() if "skipped" in t)} not subscribed (heavy types).', '']
        lines += ['## Candidates (name looks like an encoder, or a field only grows / only falls)', '']
        if candidates:
            for topic, kind, nodes, count, by_name, counters in candidates:
                lines.append(f'- `{topic}` ({kind}), {count} msgs from {nodes or "?"}: '
                             f'{"name matches; " if by_name else ""}counter-like fields: {counters or "none"}')
        else:
            lines.append('- none. Nothing the stack publishes looks like an encoder.')
        lines += ['', '## Frames the board really sent (driver counters, `rrc/frame_stats`)', '']
        if self.frame_stats_last is None:
            lines.append('No `rrc/frame_stats` seen: the driver running is not the one with the counters.')
        else:
            frames = self.frame_stats_last['frames']
            for name, entry in sorted(frames.items()):
                lines.append(f"- `{name}`: {entry['n']} frames, {entry['rate_hz']} Hz, payload {entry['len_min']}-"
                             f"{entry['len_max']} bytes, {'read by the SDK' if entry['parsed'] else 'NOBODY READS IT'}; "
                             f"samples {entry.get('samples')}")
            lines.append(f"- function bytes the SDK dropped: {self.frame_stats_last['rejected_function_bytes'] or 'none'}; "
                         f"CRC failures: {self.frame_stats_last['crc_failures']}")
            quiet = [n for n, e in frames.items() if not e['parsed']]
            lines.append('')
            lines.append('Verdict: ' + (f"the board sends {quiet} and the SDK throws it away: read those payloads."
                                        if quiet or self.frame_stats_last['rejected_function_bytes'] else
                                        'every frame the board sent is one the SDK already reads (IMU, battery, button...). '
                                        'No hidden encoder report.'))
        lines += ['', '## Servo read', '']
        if self.servo_file:
            lines.append('See `servo.csv`: compare `read_position` with `servo_cmd_us`. If it always equals the last command, '
                         'the board is answering with the position it was told, not the one the servo reached (a PWM '
                         'servo has no feedback wire). Only a reading that differs from the command, or that follows '
                         'the horn when it is moved by hand, is a measurement.')
        else:
            lines.append('Not run (`--poll-servo 0`).')
        open(os.path.join(self.out, 'report.md'), 'w').write('\n'.join(lines) + '\n')
        if self.servo_file:
            self.servo_file.close()
        self.get_logger().info(f'report: {os.path.join(self.out, "report.md")}  ({len(candidates)} candidate topics)')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--seconds', type=float, default=120.0)
    parser.add_argument('--out', default=time.strftime('~/runs/%Y%m%d-%H%M%S-encoder-probe'))
    parser.add_argument('--poll-servo', type=int, default=0, help='1: also read the PWM servo with pwm_servo/get_state')
    parser.add_argument('--poll-hz', type=float, default=1.0, help='servo read rate (1 Hz at most is sensible)')
    parser.add_argument('--channel', type=int, default=1, help="PWM channel of the steering servo (the team's J4 = 1)")
    parser.add_argument('--service', default='/rrc/pwm_servo/get_state')
    parser.add_argument('--timeout', type=float, default=1.5, help='s without an answer before the servo read is switched off')
    args = parser.parse_args()
    rclpy.init()
    node = Probe(args)
    node.create_timer(0.5, node.check_polls)
    try:
        end = time.time() + args.seconds
        while rclpy.ok() and time.time() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.finish()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
