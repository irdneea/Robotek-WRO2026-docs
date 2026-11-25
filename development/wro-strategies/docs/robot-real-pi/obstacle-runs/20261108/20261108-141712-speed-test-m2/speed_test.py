"""Floor speed per board rps (car.launch.py teleop:=true must run; car facing a wall >= 1.5 m away, straight).
python3 ~/speed_test.py 2 3 4 6      board rps to try, one push each (the operator puts the car back in between).
Each push: /cmd_vel_raw at rps / RPS_PER_MPS (base_adapter's factor) for up to PUSH s, stops at FRONT_STOP m from the
wall; speed = slope of the LiDAR front distance over the last 60 % of the push. Then 0 and a board reset (/rrc/reset):
this motor does not stop on 0."""
import math, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan, Imu
from std_msgs.msg import Empty
from rrc_lite_msgs.msg import MotorState, MotorsState

PORT = int(__import__("os").environ.get("PORT", "1"))
RPS_PER_MPS, PUSH, FRONT_STOP, FRONT_MIN_START, BACK_RPS = 4.8, 3.0, 0.45, 1.0, 2.0


class Test(Node):
    def __init__(self):
        super().__init__('speed_test')
        self.cmd = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.motor = self.create_publisher(MotorsState, '/rrc/set_motor', 10)
        self.reset = self.create_publisher(Empty, '/rrc/reset', 10)
        self.front = math.nan
        self.gz = 0.0
        self.create_subscription(LaserScan, '/robotek/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Imu, '/robotek/imu', lambda m: setattr(self, 'gz', m.angular_velocity.z), qos_profile_sensor_data)

    def on_scan(self, m):
        r = np.asarray(m.ranges)
        a = m.angle_min + m.angle_increment * np.arange(len(r))
        sel = (np.abs(np.arctan2(np.sin(a), np.cos(a))) < math.radians(4)) & np.isfinite(r) & (r > 0.05)
        self.front = float(np.median(r[sel])) if sel.any() else math.nan

    def drive(self, rps):
        """Board rps straight to rrc_driver (base_adapter stops sending after its own board reset), as base_adapter
        sends them: port 1, sign +1."""
        self.motor.publish(MotorsState(data=[MotorState(id=PORT, rps=float(rps))]))

    def spin_for(self, s):
        end = time.time() + s
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)

    def push(self, rps):
        self.spin_for(0.5)
        if not self.front >= FRONT_MIN_START:
            print(f'rps {rps}: front {self.front:.2f} m < {FRONT_MIN_START}: reversing to 1.6 m first', flush=True)
            self.back(1.6)
            if not self.front >= FRONT_MIN_START:
                return
        v = rps / RPS_PER_MPS
        samples, t0, start_front = [], time.time(), self.front
        while time.time() - t0 < PUSH and self.front > FRONT_STOP:
            self.drive(rps)
            rclpy.spin_once(self, timeout_sec=0.02)
            samples.append((time.time() - t0, self.front, self.gz))
        for _ in range(5):
            self.drive(0.0)
            self.spin_for(0.02)
        self.reset.publish(Empty())
        self.spin_for(1.0)
        t = np.array([s[0] for s in samples]); f = np.array([s[1] for s in samples])
        keep = (t >= t[-1] * 0.4) & np.isfinite(f)
        speed = -np.polyfit(t[keep], f[keep], 1)[0] if keep.sum() > 5 else math.nan
        moved = start_front - self.front
        win = [f'{t[i]:.1f}s:{(f[i]-f[j])/(t[j]-t[i]):+.2f}' for i, j in zip(range(0, len(t)-12, 12), range(12, len(t), 12))
               if np.isfinite(f[i]) and np.isfinite(f[j])]
        print('  speed per ~0.25 s window:', ' '.join(win), flush=True)
        print(f'board rps {rps:4.1f} (asked {v:.3f} m/s): steady {speed:.3f} m/s, moved {moved:.2f} m in {t[-1]:.1f} s, '
              f'yaw rate max {max(abs(s[2]) for s in samples):.2f} rad/s', flush=True)
        self.back(start_front)

    def back(self, target):
        """Reverse to where the push started (front distance), then 0 and a board reset."""
        self.spin_for(3.0 if self.front < target else 0.0)   # rrc_driver sets the board up again 2.5 s after the reset
        v = -BACK_RPS / RPS_PER_MPS
        t0 = time.time()
        while time.time() - t0 < 8.0 and self.front < target - 0.03:
            self.drive(-BACK_RPS)
            rclpy.spin_once(self, timeout_sec=0.02)
        for _ in range(5):
            self.drive(0.0)
            self.spin_for(0.02)
        self.reset.publish(Empty())
        self.spin_for(3.5)
        print(f'  back to front {self.front:.2f} m (start {target:.2f})', flush=True)


rclpy.init()
node = Test()
try:
    for i, a in enumerate(sys.argv[1:]):
        node.push(float(a))
finally:
    node.cmd.publish(Twist())
    node.reset.publish(Empty())
    rclpy.shutdown()
