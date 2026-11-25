"""
Pillar detector alone, for checking the Obstacle perception on the real car.

Runs the same perception as obstacle_strategy (color_blocks + scan_clusters +
associate) without driving, and shows it in RViz:

- /obstacle/markers (MarkerArray, scan frame): red/green cylinder for each
  associated pillar, a ray for each colour blob seen by the camera and a grey
  dot for each pillar-sized lidar cluster.
- /obstacle/debug_image/compressed (JPEG): camera with the colour boxes; only
  encoded while someone is subscribed.

- /obstacle/steer (Float32, rad, +left): bench test of the passing rule. The
  nearest sign decides: red -> pass on its right (steer right), green -> on its
  left (steer left); nothing seen -> 0 (centre). Nearest = closest associated
  pillar; if none is associated (camera not calibrated yet), the tallest colour
  box. servo_steer (robotek_hardware) turns it into the servo command.

Inputs: scan with 0 rad straight ahead (scan_adapter) and the camera image.

Colours: the simulated red range also took the real brown wood floor and
skirting board, so red uses its own HSV parameters here (measured 7 oct 2026:
red pillar H 0+-2, S >= 229, V 158-177; floor H 4-21, S 76-144; skirting board
H 0-5, V 16-70). Green: the simulated range took the pillar's yellowish
reflection on the floor (H 35-53; pillar H 60-78, S >= 221, V 66-108). In shadow
the red pillar (V 34-61) cannot be told from the skirting board (V 1-46) by
colour: it needs more light. min_area drops specks (a 5x10 cm pillar at
2.5 m is ~11x22 px). All are read on every frame: tune live with ros2 param set.
"""
import math

import cv2
from cv_bridge import CvBridge
from geometry_msgs.msg import Point
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, Image, LaserScan
from std_msgs.msg import Float32
from visualization_msgs.msg import Marker, MarkerArray

from .obstacle_field import CAMERA_HFOV, CAMERA_OFFSET_X, CAMERA_PITCH, LIDAR_OFFSET_X
from .obstacle_perception import associate, color_blocks, scan_clusters

RGB = {'red': (1.0, 0.1, 0.1), 'green': (0.1, 0.9, 0.1)}
BGR = {'red': (0, 0, 255), 'green': (0, 255, 0)}
RAY_LENGTH = 2.5   # m, same reach as scan_clusters
SYNC_GATE = .15    # s between image and scan, as in obstacle_strategy
PASS_SIDE = {'red': -1.0, 'green': 1.0}   # red: keep right of it; green: keep left


def stamp_of(msg):
    return msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9


class ObstacleDetectorNode(Node):
    def __init__(self):
        super().__init__('obstacle_detector')
        self.jpeg_quality = int(self.declare_parameter('jpeg_quality', 50).value)
        for name, value in (('red_h_max', 4), ('red_h_min_wrap', 172),
                            ('red_s_min', 170), ('red_v_min', 110),
                            ('green_h_min', 56), ('green_h_max', 90),
                            ('green_s_min', 150), ('green_v_min', 50), ('min_area', 150),
                            ('steer_deg', 25.0), ('camera_hfov', CAMERA_HFOV), ('camera_pitch', CAMERA_PITCH), ('camera_yaw', 0.0)):
            self.declare_parameter(name, value)
        self.bridge = CvBridge()
        self.scan = None
        self.markers = self.create_publisher(MarkerArray, '/obstacle/markers', 10)
        self.debug = self.create_publisher(CompressedImage, '/obstacle/debug_image/compressed', 10)
        self.steer = self.create_publisher(Float32, '/obstacle/steer', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Image, '/camera/image', self.on_image, qos_profile_sensor_data)
        self.get_logger().info('Detector de pilares listo (/obstacle/markers, /obstacle/debug_image)')

    def on_scan(self, msg):
        self.scan = msg

    def on_image(self, msg):
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        blocks = color_blocks(bgr, self.color_ranges(), int(self.get_parameter('min_area').value),
                              float(self.get_parameter('camera_hfov').value),
                              float(self.get_parameter('camera_pitch').value),
                              float(self.get_parameter('camera_yaw').value))
        synced = self.scan is not None and abs(stamp_of(msg)-stamp_of(self.scan)) <= SYNC_GATE
        clusters = scan_clusters(self.scan) if synced else []
        observations = associate(blocks, clusters) if synced else []
        decision = self.decide(blocks, observations)
        steer = math.radians(float(self.get_parameter('steer_deg').value))
        self.steer.publish(Float32(data=PASS_SIDE[decision[0]]*steer if decision else 0.0))
        if self.scan is not None:
            self.publish_markers(blocks, clusters, observations)
        if self.debug.get_subscription_count() > 0:
            self.publish_debug(msg, bgr, blocks, observations, synced, decision)

    @staticmethod
    def decide(blocks, observations):
        """(colour, source) of the nearest sign, or None."""
        if observations:
            nearest = min(observations, key=lambda o: math.hypot(o['x'], o['y']))
            return nearest['color'], f"pilar a {math.hypot(nearest['x'], nearest['y']):.2f} m"
        if blocks:
            return max(blocks, key=lambda b: b['box'][3])['color'], 'solo camara'
        return None

    def color_ranges(self):
        p = {n: int(self.get_parameter(n).value)
             for n in ('red_h_max', 'red_h_min_wrap', 'red_s_min', 'red_v_min',
                       'green_h_min', 'green_h_max', 'green_s_min', 'green_v_min')}
        s, v = p['red_s_min'], p['red_v_min']
        red = [((0, s, v), (p['red_h_max'], 255, 255)), ((p['red_h_min_wrap'], s, v), (179, 255, 255))]
        green = [((p['green_h_min'], p['green_s_min'], p['green_v_min']), (p['green_h_max'], 255, 255))]
        return {'red': red, 'green': green}

    def marker(self, ns, index, kind):
        m = Marker()
        m.header.frame_id = self.scan.header.frame_id
        m.header.stamp = self.scan.header.stamp
        m.ns, m.id, m.type, m.action = ns, index, kind, Marker.ADD
        m.pose.orientation.w = 1.0
        m.lifetime.nanosec = 500_000_000
        return m

    def publish_markers(self, blocks, clusters, observations):
        """Positions are base_link (scan_clusters); the scan frame sits LIDAR_OFFSET_X ahead."""
        out = MarkerArray()
        clear = Marker()
        clear.action = Marker.DELETEALL
        out.markers.append(clear)
        for i, obs in enumerate(observations):
            m = self.marker('pilares', i, Marker.CYLINDER)
            m.pose.position.x, m.pose.position.y = obs['x']-LIDAR_OFFSET_X, obs['y']
            m.pose.position.z = .05
            m.scale.x, m.scale.y, m.scale.z = .05, .05, .1
            m.color.r, m.color.g, m.color.b = RGB[obs['color']]
            m.color.a = .9
            out.markers.append(m)
            label = self.marker('distancias', i, Marker.TEXT_VIEW_FACING)
            label.pose.position = m.pose.position
            label.pose.position.z = .16
            label.scale.z = .06
            label.color.r = label.color.g = label.color.b = label.color.a = 1.0
            label.text = f"{obs['color']} {math.hypot(obs['x'], obs['y']):.2f} m"
            out.markers.append(label)
        for i, block in enumerate(blocks):
            m = self.marker('rayos_camara', i, Marker.LINE_LIST)
            x0 = CAMERA_OFFSET_X-LIDAR_OFFSET_X
            m.points = [self.point(x0, 0.0), self.point(x0+RAY_LENGTH*math.cos(block['bearing']),
                                                         RAY_LENGTH*math.sin(block['bearing']))]
            m.scale.x = .008
            m.color.r, m.color.g, m.color.b = RGB[block['color']]
            m.color.a = .6
            out.markers.append(m)
        dots = self.marker('clusters_lidar', 0, Marker.SPHERE_LIST)
        dots.points = [self.point(c['x']-LIDAR_OFFSET_X, c['y']) for c in clusters]
        dots.scale.x = dots.scale.y = dots.scale.z = .03
        dots.color.r = dots.color.g = dots.color.b = .7
        dots.color.a = .8
        out.markers.append(dots)
        self.markers.publish(out)

    @staticmethod
    def point(x, y):
        return Point(x=float(x), y=float(y), z=0.02)

    def publish_debug(self, msg, bgr, blocks, observations, synced, decision):
        for block in blocks:
            x, y, w, h = block['box']
            matched = any(obs['box'] == block['box'] for obs in observations)
            cv2.rectangle(bgr, (x, y), (x+w, y+h), BGR[block['color']], 3 if matched else 1)
            cv2.putText(bgr, f"{block['color']} {math.degrees(block['bearing']):+.0f}deg",
                        (x, max(15, y-4)), cv2.FONT_HERSHEY_SIMPLEX, .5, BGR[block['color']], 1)
        status = f'manchas={len(blocks)} pilares={len(observations)}'
        if not synced:
            status += ' (sin scan sincronizado)'
        cv2.putText(bgr, status, (8, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 0), 2)
        if decision:
            text = ('DERECHA' if decision[0] == 'red' else 'IZQUIERDA') + f' ({decision[1]})'
            cv2.putText(bgr, text, (8, 50), cv2.FONT_HERSHEY_SIMPLEX, .6, BGR[decision[0]], 2)
        else:
            cv2.putText(bgr, 'CENTRO', (8, 50), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        ok, jpg = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if ok:
            out = CompressedImage()
            out.header = msg.header
            out.format = 'bgr8; jpeg compressed bgr8'
            out.data = jpg.tobytes()
            self.debug.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
