import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep("  * Comparte el USB2 con el lidar.",
    "  * Tambien publica /usb_cam/image_raw/compressed (JPEG, calidad jpeg_quality)\n"
    "    para verla en RViz por Wi-Fi; solo comprime si alguien esta suscrito.\n"
    "  * Comparte el USB2 con el lidar.")
rep("from sensor_msgs.msg import Image\n",
    "from sensor_msgs.msg import CompressedImage, Image\n")
rep("        self.brightness = int(self.declare_parameter('brightness', 32).value)  # -64..64\n",
    "        self.brightness = int(self.declare_parameter('brightness', 32).value)  # -64..64\n"
    "        self.jpeg_quality = int(self.declare_parameter('jpeg_quality', 50).value)  # 1..100\n")
rep("        self.pub = self.create_publisher(Image, 'usb_cam/image_raw', 10)\n",
    "        self.pub = self.create_publisher(Image, 'usb_cam/image_raw', 10)\n"
    "        self.pub_jpeg = self.create_publisher(\n"
    "            CompressedImage, 'usb_cam/image_raw/compressed', 10)\n")
rep("        self.pub.publish(msg)\n",
    "        self.pub.publish(msg)\n"
    "\n"
    "        # JPEG solo si alguien lo pide (p. ej. RViz en otra PC): no gasta CPU en carrera.\n"
    "        if self.pub_jpeg.get_subscription_count() > 0:\n"
    "            ok, jpg = cv2.imencode(\n"
    "                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])\n"
    "            if ok:\n"
    "                comp = CompressedImage()\n"
    "                comp.header = msg.header\n"
    "                comp.format = 'bgr8; jpeg compressed bgr8'\n"
    "                comp.data = jpg.tobytes()\n"
    "                self.pub_jpeg.publish(comp)\n")
open(p, 'w').write(s)
