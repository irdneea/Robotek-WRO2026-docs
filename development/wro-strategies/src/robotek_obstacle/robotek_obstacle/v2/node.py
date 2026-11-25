"""Obstacle v2 strategy node: the same node name, topics and files as ``obstacle_strategy``.

Honest inputs only, as on the real car: LiDAR (/scan), gyro (/imu, integrated for heading) and
camera (/camera/image). Distance from LiDAR scan matching, each scan stamp aligned once (the
simulation delivers a stamp several times). The decisions are in ``v2.mission.Mission``; this
node wires the sensors to it at 50 Hz, publishes /cmd_vel and writes the same evidence files as
the current node (telemetry columns, events, detections, camera, planner, trace), so the
runner, the audit recorders and the judge work unchanged.

    ros2 launch robotek_bringup obstacle_challenge.launch.py strategy:=obstacle_strategy_v2
"""
from dataclasses import asdict, fields
import math
import signal
import time

import cv2
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image, Imu, LaserScan
from std_msgs.msg import Bool, String

from robotek_common.lidar_odometry import LidarOdometry
from robotek_common.vehicle import CAMERA_HFOV, CAMERA_PITCH, DISTANCE_MODEL_ACCEL, WHEELBASE
from ..obstacle_field import wrap
from ..obstacle_perception import associate, color_blocks, scan_clusters
from ..obstacle_recording import ObstacleRecording
from .mission import Mission
from .settings import Params

CONTROL_PERIOD = 0.02   # s
SENSOR_MAX_AGE = 0.35   # s; older data pauses the mission
ROUND_LIMIT = 180.0     # s after start (rules 9.2)
NODE_DEFAULTS = dict(telemetry_path='', done_hold=32.0, direction='auto', auto_start=True,
                     camera_hfov=CAMERA_HFOV, camera_pitch=CAMERA_PITCH, camera_yaw=0.0)


def stamp_of(msg):
    return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9


class ObstacleV2Node(Node):
    def __init__(self):
        super().__init__('obstacle_strategy')
        mission_names = [f.name for f in fields(Params)]
        defaults = {**asdict(Params()), **NODE_DEFAULTS}
        params = {k: self.declare_parameter(k, v).value for k, v in defaults.items()}
        self.node_params = {k: params[k] for k in NODE_DEFAULTS}
        self.done_hold = params['done_hold']
        self.auto_start = params['auto_start']
        self.mission = Mission({k: params[k] for k in mission_names})
        path = params['telemetry_path'] or f'/tmp/robotek-obstacle-{int(time.time())}/telemetry.csv'
        self.recording = ObstacleRecording(path)
        self.yaw = self.gyro = 0.0
        self.yaw_zero = None
        self._imu_time = None
        self.lidar_odom = LidarOdometry(accel=DISTANCE_MODEL_ACCEL)
        self._last_speed = 0.0
        self.travelled = 0.0
        self.scan = None
        self.scan_stamp = self.image_stamp = self.imu_stamp = -math.inf
        self.state = 'WAIT_SENSORS'
        self.start_requested = False
        self.started = self.done_at = None
        self.finished = False
        self.bridge = CvBridge()
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.debug = self.create_publisher(Image, '/obstacle/debug_image', 10)
        self.state_pub = self.create_publisher(
            String, '/robotek/state', QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.state_sent = None
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.create_subscription(Image, '/camera/image', self.on_image, 10)
        self.create_subscription(Imu, '/imu', self.on_imu, 10)
        self.create_subscription(Bool, '/start', self.on_start, 10)
        self.last_log = -math.inf
        self.create_timer(CONTROL_PERIOD, self.control)

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def event(self, name):
        self.recording.event(name, self.now())

    # ------------------------------------------------------------- sensors
    def on_start(self, msg):
        if msg.data:
            self.start_requested = True

    def on_scan(self, msg):
        stamp = stamp_of(msg)
        if stamp > self.scan_stamp:
            self.lidar_odom.scan(msg, self.yaw)
            self.recording.scan(msg, stamp, self.now())
        self.scan, self.scan_stamp = msg, stamp
        self.recording.trace(k='scan', t=stamp)

    def on_imu(self, msg):
        stamp = stamp_of(msg)
        self.recording.trace(k='imu', t=stamp, wz=msg.angular_velocity.z)
        if self._imu_time is not None and 0.0 < stamp - self._imu_time < 0.2:
            self.yaw += (msg.angular_velocity.z - self.mission.gyro_bias) * (stamp - self._imu_time)
        self._imu_time = stamp
        self.gyro = msg.angular_velocity.z
        self.imu_stamp = stamp

    def on_image(self, msg):
        self.image_stamp = stamp_of(msg)
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        p = self.node_params
        blocks = color_blocks(bgr, hfov=p['camera_hfov'], pitch=p['camera_pitch'], yaw=p['camera_yaw'])
        clusters = scan_clusters(self.scan) if self.scan else []
        observations = associate(blocks, clusters) if abs(self.image_stamp - self.scan_stamp) <= 0.15 else []
        self.recording.trace(k='img', t=self.image_stamp, scan_t=self.scan_stamp, obs=observations)
        self.mission.observe(observations, self.image_stamp)
        self.recording.detections(self.image_stamp, self.now(), self.scan_stamp, blocks, clusters, observations)
        self.publish_debug(msg, bgr, blocks, observations)

    def travelled_step(self):
        """Distance since the last cycle; ignored while stopped (scan-matching noise)."""
        self.lidar_odom.command(self._last_speed, CONTROL_PERIOD)
        step = self.lidar_odom.read()
        if not self.mission.loc.ready or (abs(self._last_speed) < 0.01 and abs(self.lidar_odom.speed_model) < 0.01):
            return 0.0
        self.travelled += step
        return step

    # ------------------------------------------------------------- control
    def control(self):
        now = self.now()
        distance = self.travelled_step()
        fresh = self._fresh(now)
        if self.started is None and fresh and (self.auto_start or self.start_requested):
            self.started, self.yaw_zero, self.state = now, self.yaw, 'SETUP'
            self.event('start')
        speed, steer = self._mission_step(now, fresh, distance)
        cmd = Twist()
        cmd.linear.x = speed
        cmd.angular.z = speed * math.tan(steer) / WHEELBASE
        self.cmd.publish(cmd)
        if self.state != self.state_sent:
            self.state_sent = self.state
            self.state_pub.publish(String(data=self.state))
        self._last_speed = cmd.linear.x
        self.recording.trace(k='tick', now=now, v=cmd.linear.x, w=cmd.angular.z, state=self.state,
                             yaw=self.yaw, d=distance, steer=steer)
        self.record(now, cmd)
        if self.state == 'FAULT' or (self.done_at is not None and now - self.done_at >= self.done_hold):
            self.finished = True

    def _fresh(self, now):
        """Scan, image and IMU all younger than SENSOR_MAX_AGE."""
        return (self._imu_time is not None
                and all(0 <= now - t < SENSOR_MAX_AGE for t in (self.scan_stamp, self.image_stamp, self.imu_stamp)))

    def _mission_step(self, now, fresh, distance):
        """(speed, steer) of this cycle; the state goes to FAULT, WAIT_SENSOR or the mission's."""
        if self.started is None or self.state in ('DONE', 'FAULT'):
            return 0.0, 0.0
        if now - self.started > ROUND_LIMIT:
            self.state = 'FAULT'
            self.event('timeout')
            return 0.0, 0.0
        if not fresh:
            self.state = 'WAIT_SENSOR'
            return 0.0, 0.0
        speed, steer, state = self.mission.step(
            now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, distance)
        self._record_parking(now)
        # The judge calls the final state DONE (the v2 calls it STOP).
        self.state = 'DONE' if state == 'STOP' else state
        if self.state == 'DONE':
            self.done_at = now
            self.event('done')
        return speed, steer

    def _record_parking(self, now):
        parking = self.mission.parking
        if parking is not None:
            for record in parking.log:
                self.recording.record(sim_time=now, **record)
            parking.log.clear()

    # ----------------------------------------------------------- evidence
    def record(self, now, cmd):
        m = self.mission
        x, y, th = m.pose
        self.recording.control(
            now, state=self.state, selected_direction=m.selected_direction,
            x_track=x, y_track=y, th_track=th, progress=m.phi,
            yaw_relative=wrap(self.yaw - (self.yaw_zero or 0.0)), gyro=self.gyro,
            v_cmd=cmd.linear.x, w_cmd=cmd.angular.z,
            scan_age=now - self.scan_stamp, image_age=now - self.image_stamp,
            travelled=self.travelled, lidar_odom_quality=self.lidar_odom.last_quality)
        snapshot = dict(pillar=m.pillar, profile=m.profile[:12],
                        seats={str(k / 2.0): [v[0], v[1], v[2]] for k, v in m._seats.items()},
                        parking=None if m.parking is None else dict(state=m.parking.state, plans=m.parking.plans,
                                                                                moves=m.parking.driven))
        self.recording.planner(now, snapshot)
        if now - self.last_log >= 0.5:
            self.get_logger().info(f'[{self.state}] pose=({x:.3f},{y:.3f},{th:.3f}) phi={m.phi:.2f} '
                                   f'v={cmd.linear.x:.2f} travelled={self.travelled:.2f}')
            self.last_log = now

    def publish_debug(self, msg, bgr, blocks, observations):
        for block in blocks:
            x, y, w, h = block['box']
            color = (0, 255, 0) if block['color'] == 'green' else (0, 0, 255)
            cv2.rectangle(bgr, (x, y), (x + w, y + h), color, 2)
            cv2.putText(bgr, block['color'], (x, max(15, y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.putText(bgr, f'{self.state} associated={len(observations)}',
                    (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        debug = self.bridge.cv2_to_imgmsg(bgr, 'bgr8')
        debug.header = msg.header
        self.debug.publish(debug)
        self.recording.camera(bgr, self.now())

    def close(self):
        self.cmd.publish(Twist())
        self.recording.close()


def main(args=None):
    interrupted = False

    def stop(signum, frame):
        nonlocal interrupted
        interrupted = True
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    node = ObstacleV2Node()
    try:
        while rclpy.ok() and not interrupted and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
