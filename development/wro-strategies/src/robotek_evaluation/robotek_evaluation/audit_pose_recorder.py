"""Audit-only recorder of simulator ground truth for honest runs.

In honest mode the strategy never receives /odom_gt, /odom or /joint_states. This
node records them to <output_dir>/audit_pose.csv so the rule judge, margins and the
wheel-odometry comparison can still be evaluated after the round. It never publishes.
"""
import csv
import math
from pathlib import Path
import time

from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


def yaw_of(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))


class AuditPoseRecorder(Node):
    def __init__(self):
        super().__init__('audit_pose_recorder')
        directory = Path(self.declare_parameter('output_dir', '').value)
        directory.mkdir(parents=True, exist_ok=True)
        self.file = (directory/'audit_pose.csv').open('w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['wall_time', 'sim_time', 'x_gt', 'y_gt', 'yaw_gt',
                              'steer_actual', 'steer_right_actual', 'x_odom', 'y_odom'])
        self.steer = (math.nan, math.nan)
        self.odom = (math.nan, math.nan)
        self.create_subscription(Odometry, '/odom', self.on_odom, 50)
        self.create_subscription(Odometry, '/odom_gt', self.on_gt, 50)
        self.create_subscription(JointState, '/joint_states', self.on_joints, 50)

    def on_joints(self, msg):
        values = dict(zip(msg.name, msg.position))
        self.steer = (values.get('front_left_steering_joint', math.nan),
                      values.get('front_right_steering_joint', math.nan))

    def on_odom(self, msg):
        self.odom = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    def on_gt(self, msg):
        p = msg.pose.pose.position
        self.writer.writerow([time.time(), self.get_clock().now().nanoseconds*1e-9,
                              p.x, p.y, yaw_of(msg.pose.pose.orientation), *self.steer, *self.odom])


def main():
    rclpy.init()
    node = AuditPoseRecorder()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, RuntimeError):
        pass
    finally:
        node.file.close()
