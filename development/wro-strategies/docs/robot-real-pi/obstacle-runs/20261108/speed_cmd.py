"""Floor speed through base_adapter: /cmd_vel_raw at each asked m/s for up to 3 s (stop 0.45 m from the wall), speed
from the LiDAR front per 0.25 s window, then a plain 0 (how far it rolls), then back to the start at -0.2 m/s.
python3 ~/speed_cmd.py 0.15 0.25 0.4 0.6     (car.launch.py teleop:=true running, car facing a wall >= 2 m away)"""
import math, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist, Vector3
from sensor_msgs.msg import LaserScan


class T(Node):
    def __init__(self):
        super().__init__('speed_cmd')
        self.cmd = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.front = math.nan
        self.create_subscription(LaserScan, '/robotek/scan', self.on_scan, qos_profile_sensor_data)

    def on_scan(self, m):
        r = np.asarray(m.ranges)
        a = m.angle_min + m.angle_increment * np.arange(len(r))
        sel = (np.abs(np.arctan2(np.sin(a), np.cos(a))) < math.radians(4)) & np.isfinite(r) & (r > 0.05)
        self.front = float(np.median(r[sel])) if sel.any() else math.nan

    def spin_for(self, s, v=None):
        end = time.time() + s
        while time.time() < end:
            if v is not None:
                self.cmd.publish(Twist(linear=Vector3(x=float(v))))
            rclpy.spin_once(self, timeout_sec=0.02)

    def drive(self, v, seconds, until):
        out, t0 = [], time.time()
        while time.time() - t0 < seconds and until(self.front):
            self.cmd.publish(Twist(linear=Vector3(x=float(v))))
            rclpy.spin_once(self, timeout_sec=0.05)
            out.append((time.time() - t0, self.front))
        return out


rclpy.init()
n = T()
try:
    for a in sys.argv[1:]:
        v = float(a)
        n.spin_for(0.5, 0.0)
        start = n.front
        if not start >= 1.2:
            print(f'front {start:.2f} m: too close'); break
        s = n.drive(v, 3.0, lambda f: f > 0.45)
        at_zero = n.front
        n.spin_for(1.5, 0.0)
        t = np.array([x[0] for x in s]); f = np.array([x[1] for x in s])
        win = [(f[i] - f[i + 5]) / (t[i + 5] - t[i]) for i in range(0, len(t) - 5, 5)
               if np.isfinite(f[i]) and np.isfinite(f[i + 5]) and abs(f[i] - f[i + 5]) < 0.5]
        steady = float(np.median(win[len(win) // 3:])) if len(win) > 3 else math.nan
        print(f'asked {v:.2f} m/s: steady {steady:.3f} m/s, moved {start - at_zero:.2f} m, rolled {at_zero - n.front:+.2f} m '
              f'after the 0; windows ' + ' '.join(f'{w:.2f}' for w in win), flush=True)
        n.drive(-0.2, 10.0, lambda f: f < start - 0.03)
        n.spin_for(1.5, 0.0)
        print(f'  back at {n.front:.2f} m (start {start:.2f})', flush=True)
finally:
    n.cmd.publish(Twist())
    rclpy.shutdown()
