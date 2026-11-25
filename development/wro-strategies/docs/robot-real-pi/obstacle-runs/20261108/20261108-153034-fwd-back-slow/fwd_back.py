"""Quick check: board rps 1, 2, 3 forward and backward, 1 s each (M2, robotek-learn SDK = what base_adapter sends,
x0.75 inside), a plain 0 for 1 s between; speed from the LiDAR front distance. Only the LiDAR runs in ROS."""
import math, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
sys.path.insert(0, '/home/user/robotek-learn/src/rrc_lite_driver/rrc_lite_driver')
from rrc_lite_driver_sdk.board import Board


class L(Node):
    def __init__(self):
        super().__init__('fwd_back')
        self.front, self.back = math.nan, math.nan
        self.create_subscription(LaserScan, '/robotek/scan', self.cb, qos_profile_sensor_data)

    def cb(self, m):
        r = np.asarray(m.ranges); a = m.angle_min + m.angle_increment * np.arange(len(r)); a = np.arctan2(np.sin(a), np.cos(a))
        ok = np.isfinite(r) & (r > 0.05)
        f = ok & (np.abs(a) < math.radians(4)); b = ok & (np.abs(np.abs(a) - math.pi) < math.radians(6))
        self.front = float(np.median(r[f])) if f.any() else math.nan
        self.back = float(np.median(r[b])) if b.any() else math.nan

    def spin_for(self, s, board=None, rps=None):
        end = time.time() + s
        while time.time() < end:
            if board is not None:
                board.set_motor_speed([[2, rps]])
            rclpy.spin_once(self, timeout_sec=0.04)


rclpy.init(); n = L()
b = Board(device='/dev/rrc_lite'); b.enable_reception(); n.spin_for(0.8)
print(f'start: front {n.front:.2f} m, back {n.back:.2f} m, battery {b.get_battery()} mV', flush=True)
try:
    plan = [(float(a[:-1]), 1 if a[-1] == 'f' else -1) for a in (sys.argv[1:] or ['1f', '1b', '2f', '2b', '3f', '3b'])]
    for rps, sign in plan:
        name = 'forward' if sign > 0 else 'backward'
        if True:
            f0, b0 = n.front, n.back
            if (sign > 0 and not f0 > 0.8) or (sign < 0 and f0 > 2.4):   # no rear LiDAR: back only while the front wall is near
                print(f'{rps:.0f} rps {name}: not enough room (front {f0:.2f}, back {b0:.2f})', flush=True); continue
            dur = max(1.0, 1.0 / rps)              # the same distance at every rps: 1 s at 1 rps, 10 s at 0.1
            samples, t0 = [], time.time()
            while time.time() - t0 < dur:
                b.set_motor_speed([[2, sign * rps]])
                rclpy.spin_once(n, timeout_sec=0.04)
                samples.append((time.time() - t0, n.front))
            f1, b1 = n.front, n.back
            t = np.array([x[0] for x in samples]); fr = np.array([x[1] for x in samples]); half = (t >= dur / 2) & np.isfinite(fr)
            steady = -np.polyfit(t[half], fr[half], 1)[0] if half.sum() > 5 else math.nan
            n.spin_for(1.0, b, 0.0)
            f2 = n.front
            moved = f0 - f1
            print(f'{rps:.1f} rps {name:8s} {dur:4.1f} s: moved {moved:+.2f} m, steady (2nd half) {steady:+.3f} m/s '
                  f'(4.4 rps per m/s would be {sign * rps / 4.4:+.3f}), rolled {f1 - f2:+.2f} m after the 0', flush=True)
finally:
    for _ in range(10):
        b.set_motor_speed([[2, 0.0]]); time.sleep(0.05)
    rclpy.shutdown()
