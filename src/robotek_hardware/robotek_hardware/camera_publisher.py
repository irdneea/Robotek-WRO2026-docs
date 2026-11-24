#!/usr/bin/env python3
"""Publishes a USB webcam on /usb_cam/image_raw (ROS 2).

If the camera is missing, or unplugged while running, the node does not crash: it says so clearly and retries every
`reopen_retry` seconds until the camera is back. With `device:=''` (the default) it finds the camera by itself: the
first /dev/v4l/by-id/*-video-index0 and, if there is none, /dev/video0.

The node was written for one specific camera, measured with `v4l2-ctl --list-ctrls` and `--list-formats-ext`:
  * It only delivers YUYV 640x480 (no MJPG). We do not ask for MJPG: the request would fail silently and the driver
    would fall back to YUYV anyway.
  * It has no 'gain' control, so light is regulated with the exposure.
  * It also publishes /usb_cam/image_raw/compressed (JPEG, quality `jpeg_quality`) to watch it in RViz over Wi-Fi.
    It only compresses while somebody is subscribed.
  * It shares a USB 2 controller with the LiDAR, hence 15 fps and a buffer of one frame: we do not want to take
    bandwidth from the sensor that keeps the car from crashing.

By default the camera stays in AUTO (auto exposure and auto white balance), which looks best to the eye. When you tune
HSV colours and need brightness and hue that do not drift from frame to frame, start it with:

    ros2 run <package> camera_publisher --ros-args -p manual:=true

Careful: the camera's controls PERSIST between runs. If a previous run left it in manual and dark, opening it
"without touching anything" inherits that state and the picture looks bad for no visible reason. That is why this node
ALWAYS sets the mode it wants explicitly (auto or manual), so it starts the same way every time.
"""

import glob
import math
import os
import shutil
import subprocess
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import CompressedImage, Image


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        # Find the camera by USB id, not by /dev/videoN: the Pi 5 has about 19 video nodes of its own (codec,
        # pisp_be) and the number of the USB camera changes with the boot order. index0 is the capture node and
        # index1 the metadata one. An empty value means "find it yourself".
        self.device_param = str(self.declare_parameter('device', '').value)
        self.device = self._find_device()
        self.width = int(self.declare_parameter('width', 640).value)
        self.height = int(self.declare_parameter('height', 480).value)
        self.fps = int(self.declare_parameter('fps', 15).value)
        self.manual = bool(self.declare_parameter('manual', False).value)
        # These three are only used with manual:=true.
        self.exposure = int(
            self.declare_parameter('exposure_absolute', 120).value)  # units of 100 us: 120 = 12 ms
        self.wb_temp = int(
            self.declare_parameter('white_balance_temperature', 4000).value)
        self.brightness = int(self.declare_parameter('brightness', 32).value)  # -64..64
        self.jpeg_quality = int(self.declare_parameter('jpeg_quality', 50).value)  # 1..100
        # The camera is mounted upside down on our car (1 Nov 2026): rotate the picture 180 degrees before publishing.
        self.rotate_180 = bool(self.declare_parameter('rotate_180', False).value)
        # Lens correction (barrel distortion) with a one-coefficient radial model, and a crop to the field of view of
        # the simulated camera, so the car's picture looks like Gazebo's (straight lines straight, same angle).
        # camera_f and camera_k1 were tuned on 1 Nov 2026 until the edge of the far wall came out straight, with the
        # field of view the team measured (66.7 degrees); output_hfov_deg = 60 is the simulation's.
        self.undistort = bool(self.declare_parameter('undistort', False).value)
        self.camera_f = float(self.declare_parameter('camera_f', 570.).value)
        self.camera_k1 = float(self.declare_parameter('camera_k1', -0.34).value)
        self.output_hfov_deg = float(self.declare_parameter('output_hfov_deg', 60.).value)
        self._maps = None

        # When the camera is unplugged the open descriptor goes dead: after `reopen_after` failures in a row the node
        # reopens it by itself, trying every `reopen_retry` seconds (0 disables it).
        self.reopen_after = int(self.declare_parameter('reopen_after', 30).value)
        self.reopen_retry = float(self.declare_parameter('reopen_retry', 1.0).value)
        self._last_retry = 0.0

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, 'usb_cam/image_raw', 10)
        self.pub_jpeg = self.create_publisher(
            CompressedImage, 'usb_cam/image_raw/compressed', 10)
        self._failures = 0
        self.cap = None
        self._open()
        self.timer = self.create_timer(1.0 / max(1, self.fps), self._publish)

    def _find_device(self):
        """The requested device; otherwise the first camera by USB id; otherwise /dev/video0."""
        if self.device_param:
            return self.device_param
        by_id = sorted(glob.glob('/dev/v4l/by-id/*-video-index0'))
        return by_id[0] if by_id else '/dev/video0'

    def _open(self):
        """Tries to open the camera. Without one it warns clearly (every reopen_retry s) and keeps trying."""
        self.device = self._find_device()
        if not os.path.exists(self.device):
            self.get_logger().warn(
                f'Camera not found ({self.device} does not exist): plug it in. Retrying every '
                f'{self.reopen_retry:g} s. Check with: ls /dev/v4l/by-id/ and v4l2-ctl --list-devices',
                throttle_duration_sec=10.0)
            return False
        cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not cap.isOpened():
            self.get_logger().warn(
                f'Could not open the camera {self.device} (permissions? the user must be in the "video" group, '
                f'or another program is using it). Retrying every {self.reopen_retry:g} s',
                throttle_duration_sec=10.0)
            cap.release()
            return False
        self.cap = cap
        self._configure_capture()
        self._configure_image()
        self.get_logger().info(
            f'Camera {self.device} '
            f'{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x'
            f'{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ '
            f'{self.cap.get(cv2.CAP_PROP_FPS):.0f} fps, '
            f'mode={"manual" if self.manual else "auto"}')
        return True

    def _configure_capture(self):
        """Format, resolution, fps and buffer. Every setting is checked: one that fails must show in the log, not
        be guessed."""
        settings = [
            (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'), 'FOURCC'),
            (cv2.CAP_PROP_FRAME_WIDTH, self.width, 'WIDTH'),
            (cv2.CAP_PROP_FRAME_HEIGHT, self.height, 'HEIGHT'),
            (cv2.CAP_PROP_FPS, self.fps, 'FPS'),
            (cv2.CAP_PROP_BUFFERSIZE, 1, 'BUFFERSIZE'),  # always the freshest frame
        ]
        for prop, value, name in settings:
            if not self.cap.set(prop, value):
                self.get_logger().warn(f'The camera rejected {name}={value}')

    def _configure_image(self):
        """Sets exposure and white balance BY NAME with v4l2-ctl.

        cap.set(CAP_PROP_EXPOSURE) is ambiguous between OpenCV builds (sometimes 100 us, sometimes log2 of seconds)
        and fails silently. v4l2-ctl writes the control by name and it can be read back to confirm.
        """
        if shutil.which('v4l2-ctl') is None:
            self.get_logger().warn(
                'v4l2-ctl is not installed: the camera stays as the last run left it '
                '(it may look dark or with odd colours).')
            return

        if self.manual:
            # Order matters: mode first, value after. With auto exposure on, exposure_time_absolute is inactive
            # and the value is dropped without a warning.
            ctrls = [
                ('auto_exposure', 1),                 # 1 = Manual
                ('exposure_time_absolute', self.exposure),
                ('white_balance_automatic', 0),
                ('white_balance_temperature', self.wb_temp),
                ('brightness', self.brightness),
            ]
        else:
            # AUTO looks best. Reset it explicitly in case a previous run left the camera dark and in manual
            # (the controls persist).
            ctrls = [
                ('auto_exposure', 3),                 # 3 = Aperture Priority (auto)
                ('white_balance_automatic', 1),
                ('brightness', 0),                    # clears any old offset
            ]

        for name, value in ctrls:
            try:
                subprocess.run(
                    ['v4l2-ctl', '-d', self.device, '--set-ctrl', f'{name}={value}'],
                    check=True, capture_output=True, timeout=2.0)
            except Exception as e:                    # noqa: BLE001
                self.get_logger().warn(f'Could not set {name}={value}: {e}')

        # Read back only what was set, to confirm it was applied.
        names = ','.join(n for n, _ in ctrls)
        try:
            r = subprocess.run(
                ['v4l2-ctl', '-d', self.device, '--get-ctrl', names],
                check=True, capture_output=True, text=True, timeout=2.0)
            self.get_logger().info(
                'Controls -> ' + r.stdout.strip().replace('\n', ' | '))
        except Exception as e:                        # noqa: BLE001
            self.get_logger().warn(f'Could not verify the controls: {e}')

    def _reopen(self):
        """Releases the dead (or missing) descriptor and reopens the camera, at most once every reopen_retry s."""
        now = time.monotonic()
        if now - self._last_retry < self.reopen_retry:
            return
        self._last_retry = now
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self._open():
            self.get_logger().info(f'Camera reopened after {self._failures} failures in a row')

    def _publish(self):
        if self.cap is None:
            self._failures += 1
            self._reopen()
            return
        ret, frame = self.cap.read()
        if ret and self.rotate_180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        if ret and self.undistort:
            frame = self._correct(frame)
        if not ret:
            # A warning for every lost frame floods the log: warn once every 30.
            if self._failures % 30 == 0:
                self.get_logger().warn(f'Failed to capture a frame (x{self._failures + 1})')
            self._failures += 1
            if self.reopen_after > 0 and self._failures >= self.reopen_after:
                self._reopen()
            return
        self._failures = 0
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self.pub.publish(msg)

        # JPEG only when somebody asks for it (for example RViz on another computer): no CPU spent during a round.
        if self.pub_jpeg.get_subscription_count() > 0:
            ok, jpg = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
            if ok:
                comp = CompressedImage()
                comp.header = msg.header
                comp.format = 'bgr8; jpeg compressed bgr8'
                comp.data = jpg.tobytes()
                self.pub_jpeg.publish(comp)

    def _correct(self, frame):
        """Lens-corrected frame, cropped to output_hfov_deg (the maps are computed once per image size)."""
        h, w = frame.shape[:2]
        if self._maps is None or self._maps[0] != (w, h):
            K = np.array([[self.camera_f, 0, w / 2], [0, self.camera_f, h / 2], [0, 0, 1]], np.float64)
            fo = (w / 2) / math.tan(math.radians(self.output_hfov_deg) / 2)
            P = np.array([[fo, 0, w / 2], [0, fo, h / 2], [0, 0, 1]], np.float64)
            m1, m2 = cv2.initUndistortRectifyMap(K, np.array([self.camera_k1, 0, 0, 0], np.float64), None, P,
                                                 (w, h), cv2.CV_16SC2)
            self._maps = ((w, h), m1, m2)
        return cv2.remap(frame, self._maps[1], self._maps[2], cv2.INTER_LINEAR)

    def destroy_node(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.try_shutdown()
        except Exception:                             # noqa: BLE001
            pass


if __name__ == '__main__':
    main()
