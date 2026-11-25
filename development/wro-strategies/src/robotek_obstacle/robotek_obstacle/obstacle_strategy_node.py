"""
Obstacle Challenge strategy node (three laps, no parking).

Honest inputs only, as on the real car: LiDAR, gyro (integrated for heading)
and camera. No wheel odometry (no encoder), no simulator pose, no steering
joints: travelled distance comes from LiDAR scan matching (open_lidar_odometry).
Ground truth (car and pillars) is recorded by the audit nodes, never here.

Flow: sensors -> ObstacleMission (calibrate, direction) -> ObstacleDriver
(localize, map signs, plan, follow) -> /cmd_vel. Files: ObstacleRecording.
"""
from dataclasses import asdict
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

from .obstacle_config import ObstacleConfig
from .obstacle_field import WHEELBASE, wrap
from .obstacle_mission import ObstacleMission
from .obstacle_perception import associate, color_blocks, scan_clusters
from .obstacle_recording import ObstacleRecording
from robotek_common.vehicle import DISTANCE_MODEL_ACCEL
from robotek_common.lidar_odometry import LidarOdometry

CONTROL_PERIOD = .02  # s
SENSOR_MAX_AGE = .35  # s; older data pauses the mission
ROUND_LIMIT = 180.    # s after start


def stamp_of(msg):
    return msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9


class ObstacleStrategyNode(Node):
    def __init__(self):
        super().__init__('obstacle_strategy')
        # direction: always auto. auto_start: start on the first complete sensor set (simulation);
        # false on the real car, which waits for /start (the button).
        node_defaults = dict(telemetry_path='', done_hold=32., direction='auto', auto_start=True)
        defaults = {**asdict(ObstacleConfig()), **node_defaults}
        params = {k: self.declare_parameter(k, v).value for k, v in defaults.items()}
        self.done_hold = params['done_hold']
        self.auto_start = params['auto_start']
        self.start_requested = False
        self.mission = ObstacleMission(ObstacleConfig(**{k: params[k] for k in asdict(ObstacleConfig())}))
        path = params['telemetry_path'] or f'/tmp/robotek-obstacle-{int(time.time())}/telemetry.csv'
        self.recording = ObstacleRecording(path)
        # Heading: integrated gyro (bias from the mission's calibration).
        self.yaw = self.gyro = 0.
        self.yaw_zero = None
        self._imu_time = None
        # Distance: lidar scan matching; commanded speed only for the sign.
        self.lidar_odom = LidarOdometry(accel=DISTANCE_MODEL_ACCEL)
        self._last_speed = 0.
        self.travelled = 0.
        self.scan = None
        self.scan_stamp = self.image_stamp = self.imu_stamp = -math.inf
        self.state = 'WAIT_SENSORS'
        self.started = self.done_at = None
        self.finished = False
        self.bridge = CvBridge()
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.debug = self.create_publisher(Image, '/obstacle/debug_image', 10)
        # Display only (status RGBs on the real car): the state name, latched, on every change.
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
        return self.get_clock().now().nanoseconds*1e-9

    def event(self, name):
        self.recording.event(name, self.now())

    # ------------------------------------------------------------- sensors
    def on_start(self, msg):
        if msg.data:
            self.start_requested = True

    def on_scan(self, msg):
        self.scan, self.scan_stamp = msg, stamp_of(msg)
        self.recording.trace(k='scan', t=self.scan_stamp)
        self.lidar_odom.scan(msg, self.yaw)
        self.recording.scan(msg, self.scan_stamp, self.now())

    def on_imu(self, msg):
        stamp = stamp_of(msg)
        self.recording.trace(k='imu', t=stamp, wz=msg.angular_velocity.z)
        if self._imu_time is not None and 0. < stamp-self._imu_time < .2:
            self.yaw += (msg.angular_velocity.z-self.mission.gyro_bias)*(stamp-self._imu_time)
        self._imu_time = stamp
        self.gyro = msg.angular_velocity.z
        self.imu_stamp = stamp

    def on_image(self, msg):
        self.image_stamp = stamp_of(msg)
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.mission.image(bgr, self.image_stamp)
        cfg = self.mission.cfg
        blocks = color_blocks(bgr, hfov=cfg.camera_hfov, pitch=cfg.camera_pitch, yaw=cfg.camera_yaw)
        clusters = scan_clusters(self.scan) if self.scan else []
        observations = associate(blocks, clusters) if abs(self.image_stamp-self.scan_stamp) <= .15 else []
        self.recording.trace(k='img', t=self.image_stamp, scan_t=self.scan_stamp, obs=observations,
                             vis=self.mission.lines.direction)
        self.mission.observe(observations)
        self.recording.detections(self.image_stamp, self.now(), self.scan_stamp, blocks, clusters, observations)
        self.publish_debug(msg, bgr, blocks, observations)

    def travelled_step(self):
        """Distance since the last cycle; ignored while stopped (scan-matching noise)."""
        self.lidar_odom.command(self._last_speed, CONTROL_PERIOD)
        step = self.lidar_odom.read()
        if self.yaw_zero is None or (abs(self._last_speed) < .01 and abs(self.lidar_odom.speed_model) < .01):
            return 0.
        self.travelled += step
        return step

    # ------------------------------------------------------------- control
    def control(self):
        now = self.now()
        distance = self.travelled_step()
        speed = steer = 0.
        fresh = (self._imu_time is not None
                 and all(0 <= now-t < SENSOR_MAX_AGE for t in (self.scan_stamp, self.image_stamp, self.imu_stamp)))
        if self.started is None and fresh and (self.auto_start or self.start_requested):
            self.started, self.yaw_zero, self.state = now, self.yaw, 'CALIBRATE'
            self.event('start')
        if self.started is not None and self.state not in ('DONE', 'PARKED', 'FAULT'):
            if now-self.started > ROUND_LIMIT:
                self.state = 'FAULT'
                self.event('timeout')
            elif not fresh:
                self.state = 'WAIT_SENSOR'
            else:
                speed, steer, self.state = self.mission.step(
                    now, self.scan, self.scan_stamp, self.image_stamp, self.yaw, self.gyro, distance)
                parking = self.mission.parking
                if parking:
                    for record in parking.log:
                        self.recording.record(sim_time=now, **record)
                    parking.log.clear()
                if self.state in ('DONE', 'PARKED'):
                    self.done_at = now
                    self.event('done')
                elif self.state in ('DIRECTION_FAULT', 'PARK_FAIL'):
                    self.event(self.state.lower())
                    self.state = 'FAULT'
        cmd = Twist()
        cmd.linear.x = speed
        cmd.angular.z = speed*math.tan(steer)/WHEELBASE
        self.cmd.publish(cmd)
        if self.state != self.state_sent:
            self.state_sent = self.state
            self.state_pub.publish(String(data=self.state))
        self._last_speed = cmd.linear.x
        self.recording.trace(k='tick', now=now, v=cmd.linear.x, w=cmd.angular.z, state=self.state,
                             yaw=self.yaw, d=distance)
        self.record(now, cmd)
        if self.state == 'FAULT' or (self.done_at is not None and now-self.done_at >= self.done_hold):
            self.finished = True

    # ----------------------------------------------------------- evidence
    def record(self, now, cmd):
        driver = self.mission.driver
        pose = driver.pose() if driver else (math.nan,)*3
        self.recording.control(
            now, state=self.state, selected_direction=self.mission.selected_direction,
            x_track=pose[0], y_track=pose[1], th_track=pose[2],
            progress=driver.phi if driver else math.nan,
            yaw_relative=wrap(self.yaw-(self.yaw_zero or 0.)), gyro=self.gyro,
            v_cmd=cmd.linear.x, w_cmd=cmd.angular.z,
            scan_age=now-self.scan_stamp, image_age=now-self.image_stamp,
            travelled=self.travelled, lidar_odom_quality=self.lidar_odom.last_quality)
        if driver:
            snapshot = driver.snapshot()
            if self.mission.parking:
                snapshot['parking'] = self.mission.parking.snapshot()
            self.recording.planner(now, snapshot)
        if now-self.last_log >= .5:
            self.get_logger().info(f'[{self.state}] pose=({pose[0]:.3f},{pose[1]:.3f},{pose[2]:.3f}) '
                                   f'v={cmd.linear.x:.2f} travelled={self.travelled:.2f}')
            self.last_log = now

    def publish_debug(self, msg, bgr, blocks, observations):
        for block in blocks:
            x, y, w, h = block['box']
            color = (0, 255, 0) if block['color'] == 'green' else (0, 0, 255)
            cv2.rectangle(bgr, (x, y), (x+w, y+h), color, 2)
            cv2.putText(bgr, block['color'], (x, max(15, y)), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 1)
        cv2.putText(bgr, f'{self.state} associated={len(observations)}',
                    (8, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 0), 2)
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
    node = ObstacleStrategyNode()
    try:
        while rclpy.ok() and not interrupted and not node.finished:
            rclpy.spin_once(node, timeout_sec=.1)
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
