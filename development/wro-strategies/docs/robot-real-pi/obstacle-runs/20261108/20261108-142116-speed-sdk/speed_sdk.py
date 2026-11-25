"""Floor speed per rps with coach/ros2_hiwonder's SDK straight on the board (MentorPi style: no 0.75 factor, no
adapter, no rrc_driver). Only the LiDAR runs in ROS (car.launch.py controller:=false teleop:=true camera:=false).
PORT=2 TYPE=none|0..3 python3 ~/hw/speed_sdk.py 0.5 1 2 3
Each push: rps for up to 3 s (stops at 0.45 m from the wall), speed from the LiDAR front distance per 0.25 s window,
then 0, a board reset (RTS) and back to the start (reverse at -1 rps)."""
import math, os, sys, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct
from ros_robot_controller_sdk import Board, PacketFunction

PORT = int(os.environ.get('PORT', '2'))
TYPE = os.environ.get('TYPE', 'none')
PUSH, FRONT_STOP, BACK_RPS = 3.0, 0.45, 1.0


class Lidar(Node):
    def __init__(self):
        super().__init__('speed_sdk')
        self.front = math.nan
        self.create_subscription(LaserScan, '/robotek/scan', self.on_scan, qos_profile_sensor_data)

    def on_scan(self, m):
        r = np.asarray(m.ranges)
        a = m.angle_min + m.angle_increment * np.arange(len(r))
        sel = (np.abs(np.arctan2(np.sin(a), np.cos(a))) < math.radians(4)) & np.isfinite(r) & (r > 0.05)
        self.front = float(np.median(r[sel])) if sel.any() else math.nan

    def spin_for(self, s):
        end = time.time() + s
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)


def setup(board):
    board.enable_reception()
    if TYPE != 'none':
        for _ in range(2):
            board.buf_write(PacketFunction.PACKET_FUNC_MOTOR, struct.pack('<BB', 0x05, int(TYPE)))  # set_motor_type
            time.sleep(0.05)


def stop(board, lidar):
    for _ in range(5):
        board.set_motor_speed([[PORT, 0.0]])
        time.sleep(0.02)
    if os.environ.get('STOP') == 'zero':
        before = lidar.front
        for _ in range(30):
            board.set_motor_speed([[PORT, 0.0]])
            lidar.spin_for(0.05)
        print(f'  plain 0: rolled {before - lidar.front:+.2f} m in 1.5 s after the 0', flush=True)
        return
    board.port.rts = True
    time.sleep(0.1)
    board.port.rts = False
    lidar.spin_for(3.0)
    setup(board)


def drive(board, lidar, rps, seconds, until):
    samples, t0 = [], time.time()
    while time.time() - t0 < seconds and until(lidar.front):
        board.set_motor_speed([[PORT, rps]])
        lidar.spin_for(0.05)
        samples.append((time.time() - t0, lidar.front))
    return samples


if __name__ != '__main__':
    raise ImportError
rclpy.init()
lidar = Lidar()
board = Board(device='/dev/rrc_lite')
setup(board)
print(f'port M{PORT}, motor type {TYPE}', flush=True)
try:
    for a in sys.argv[1:]:
        rps = float(a)
        lidar.spin_for(0.5)
        start = lidar.front
        if not start >= 1.0:
            print(f'front {start:.2f} m: too close', flush=True)
            break
        s = drive(board, lidar, rps, PUSH, lambda f: f > FRONT_STOP)
        stop(board, lidar)
        t = np.array([x[0] for x in s]); f = np.array([x[1] for x in s])
        win = []
        for i in range(0, len(t) - 5, 5):
            j = i + 5
            if np.isfinite(f[i]) and np.isfinite(f[j]) and abs(f[i] - f[j]) < 0.5:
                win.append((f[i] - f[j]) / (t[j] - t[i]))
        steady = np.median(win[len(win) // 3:]) if len(win) > 3 else math.nan
        print(f'rps {rps:+.2f}: steady {steady:.3f} m/s (median of the last 2/3 of 0.25 s windows), moved '
              f'{start - lidar.front:.2f} m; windows ' + ' '.join(f'{w:.2f}' for w in win), flush=True)
        drive(board, lidar, -BACK_RPS if rps > 0 else BACK_RPS, 8.0, lambda f: f < start - 0.03)
        stop(board, lidar)
        print(f'  back at {lidar.front:.2f} m (start {start:.2f})', flush=True)
finally:
    board.set_motor_speed([[PORT, 0.0]])
    board.port.rts = True
    time.sleep(0.1)
    board.port.rts = False
    rclpy.shutdown()
