"""Power monitor for the real car: battery (RRC Lite board) and the Pi's 5 V input.

The battery feeds both the motor and the Raspberry Pi (via a 5 V regulator). This node
records, until Ctrl+C or `duration` s:
  - battery voltage from /rrc/battery (mV, as published by the board);
  - the Pi 5 input EXT5V_V (`vcgencmd pmic_read_adc`, ~100 Hz in a thread);
  - `vcgencmd get_throttled` (bit 0: under-voltage now, bit 16: it happened since boot).
into ~/robotek-runs/<UTC>-power/power.csv (t, source, value) and prints minima at the end.
Times are wall-clock seconds, like actuator_test, so both runs can be lined up.

  ros2 run robotek_hardware power_monitor --ros-args -p duration:=30.0
"""
import csv
import datetime
import os
import re
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt16

PI_MIN_V = 4.75   # below this the Pi 5 is browning out (its under-voltage flag trips at ~4.63 V)


def vcgencmd(*args):
    return subprocess.run(['vcgencmd', *args], capture_output=True, text=True, timeout=1.).stdout


class PowerMonitor(Node):
    def __init__(self):
        super().__init__('power_monitor')
        self.duration = float(self.declare_parameter('duration', 0.).value)
        run_dir = os.path.expanduser(self.declare_parameter('run_dir', '~/robotek-runs').value)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.dir = os.path.join(run_dir, f'{stamp}-power')
        os.makedirs(self.dir, exist_ok=True)
        self.file = open(os.path.join(self.dir, 'power.csv'), 'w', newline='')
        self.csv = csv.writer(self.file)
        self.csv.writerow(['t', 'source', 'value'])
        self.lock = threading.Lock()
        self.values = {'battery_v': [], 'pi_5v': []}
        self.throttled = set()
        self.start = time.time()
        self.running = True
        self.create_subscription(UInt16, '/rrc/battery', self.on_battery, 10)
        self.thread = threading.Thread(target=self.poll_pi, daemon=True)
        self.thread.start()
        self.get_logger().info(f'Registrando bateria y 5 V del Pi en {self.dir}')

    def record(self, source, value):
        with self.lock:
            self.csv.writerow([f'{time.time():.4f}', source, value])
            if source in self.values:
                self.values[source].append(value)

    def on_battery(self, msg):
        self.record('battery_v', msg.data/1000.)

    def poll_pi(self):
        n = 0
        while self.running:
            match = re.search(r'=([\d.]+)V', vcgencmd('pmic_read_adc', 'EXT5V_V'))
            if match:
                self.record('pi_5v', float(match.group(1)))
            if n % 20 == 0:   # flags ~5 Hz
                flags = int(vcgencmd('get_throttled').strip().split('=')[-1], 16)
                self.record('throttled', hex(flags))
                self.throttled.add(flags)
            n += 1
            time.sleep(.01)
            if self.duration and time.time()-self.start > self.duration:
                self.running = False

    def report(self):
        self.running = False
        self.thread.join(timeout=2.)
        with self.lock:
            self.file.flush()
            lines = []
            for source, unit in (('battery_v', 'V bateria'), ('pi_5v', 'V entrada del Pi')):
                v = self.values[source]
                if v:
                    lines.append(f'{unit}: min {min(v):.3f}  media {sum(v)/len(v):.3f}  max {max(v):.3f} '
                                 f'({len(v)} muestras)')
                else:
                    lines.append(f'{unit}: sin datos')
            pi = self.values['pi_5v']
            low = sum(1 for v in pi if v < PI_MIN_V)
            lines.append(f'muestras del Pi por debajo de {PI_MIN_V} V: {low}')
            flags = sorted(self.throttled)
            lines.append('get_throttled: ' + ', '.join(hex(f) for f in flags)
                         + (' -> HUBO BAJO VOLTAJE' if any(f & 0x50005 for f in flags) else ' (sin bajo voltaje)'))
        with open(os.path.join(self.dir, 'summary.txt'), 'w') as f:
            f.write('\n'.join(lines)+'\n')
        for line in lines:
            self.get_logger().info(line)
        self.file.close()


def main(args=None):
    rclpy.init(args=args)
    node = PowerMonitor()
    try:
        while rclpy.ok() and node.running:
            rclpy.spin_once(node, timeout_sec=.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.report()
        node.destroy_node()
        rclpy.try_shutdown()
