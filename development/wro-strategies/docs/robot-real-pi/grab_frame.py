import sys
import cv2
import rclpy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

rclpy.init()
node = rclpy.create_node('grab_frame')
done = []
def cb(msg):
    if not done:
        cv2.imwrite(sys.argv[1], CvBridge().imgmsg_to_cv2(msg, 'bgr8'))
        done.append(1)
node.create_subscription(Image, '/usb_cam/image_raw', cb, 1)
while not done:
    rclpy.spin_once(node, timeout_sec=1.0)
print('ok', sys.argv[1])
