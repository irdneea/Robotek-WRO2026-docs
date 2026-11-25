"""Floor test (8 nov 2026): drive at RPS for DRIVE s (board rps on M2, + = forward, robotek-learn SDK directly), then
stop either with a plain 0 or with a counter-pulse (opposite rps for a moment, then 0), and measure how far the car
rolls after the cut: LiDAR front distance (straight) and the integrated gyro (full lock). Only the LiDAR runs in ROS."""
import math, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
sys.path.insert(0, "/home/user/robotek-learn/src/rrc_lite_driver/rrc_lite_driver")
from rrc_lite_driver_sdk.board import Board
RPS, DRIVE, CENTER, LOCK = 1.2, 1.2, 1403, 1753     # LOCK: 17.5 deg of servo to the right (20 us per deg)


class L(Node):
    def __init__(self):
        super().__init__("brake_test")
        self.front = math.nan
        self.create_subscription(LaserScan, "/robotek/scan", self.cb, qos_profile_sensor_data)

    def cb(self, m):
        r = np.asarray(m.ranges); a = m.angle_min + m.angle_increment * np.arange(len(r)); a = np.arctan2(np.sin(a), np.cos(a))
        f = np.isfinite(r) & (r > 0.05) & (np.abs(a) < math.radians(4))
        self.front = float(np.median(r[f])) if f.any() else math.nan


rclpy.init(); n = L()
b = Board(device="/dev/rrc_lite"); b.enable_reception()
yaw = [0.0]; last = [time.time()]; bias = [0.0]


def tick(rps):
    b.set_motor_speed([[2, rps]])
    rclpy.spin_once(n, timeout_sec=0.02)
    d = b.get_imu(); now = time.time()
    if d is not None:
        yaw[0] += (math.radians(d[4]) - bias[0]) * (now - last[0]); last[0] = now


def hold(s, rps):
    end = time.time() + s
    while time.time() < end: tick(rps)


def run(servo, sign, brake):
    b.pwm_servo_set_position(0.1, [[1, servo]]); hold(0.6, 0.0)
    yaw[0] = 0.0; f0 = n.front; hold(DRIVE, sign * RPS)
    f1, y1 = n.front, yaw[0]
    if brake:
        hold(brake[1], -sign * brake[0])
    hold(1.5, 0.0)
    f2, y2 = n.front, yaw[0]
    name = "zero" if not brake else "counter %.1f rps %.2f s" % brake
    print("%-8s %-8s %-22s drove %+.3f m %+.2f rad | after the cut %+.3f m %+.3f rad (~%.3f m of arc)" % (
        "lock" if servo != CENTER else "straight", "fwd" if sign > 0 else "back", name,
        f0 - f1, y1, f1 - f2, y2 - y1, abs(y2 - y1) * 0.37), flush=True)


hold(0.8, 0.0)
yaw[0] = 0.0; t0 = time.time(); hold(2.0, 0.0); bias[0] = yaw[0] / (time.time() - t0); print("gyro bias %.4f rad/s" % bias[0])
print("start: front %.2f m, battery %s mV" % (n.front, b.get_battery()), flush=True)
try:
    for servo in (CENTER, LOCK):
        for brake in (None, (1.0, 0.15), (2.0, 0.15)):
            run(servo, 1, brake); run(servo, -1, brake)
finally:
    for _ in range(10):
        b.set_motor_speed([[2, 0.0]]); b.pwm_servo_set_position(0.1, [[1, CENTER]]); time.sleep(0.05)
    rclpy.shutdown()
