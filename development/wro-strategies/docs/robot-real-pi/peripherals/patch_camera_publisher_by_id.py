"""Aplica el cambio 'camara por id de USB' a peripherals/camera_publisher.py.

  python3 patch_camera_publisher_by_id.py ~/wro_controller_ws/src/peripherals/peripherals/camera_publisher.py

Por defecto abre /dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0 (el nodo de captura de la
camara icSpring, sea cual sea su puerto USB y su numero /dev/videoN); si ese enlace no existe,
vuelve a /dev/video0 con un aviso."""
import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


if '\nimport os\n' not in s:
    rep("\nimport cv2\n", "\nimport os\n\nimport cv2\n")
rep("        self.device = self.declare_parameter('device', '/dev/video0').value\n",
    "        # Por id de USB, no por /dev/videoN: la Pi 5 tiene ~19 nodos de video propios (codec,\n"
    "        # pisp_be) y el numero de la camara USB puede cambiar con el orden de arranque.\n"
    "        # index0 = nodo de captura; index1 es el de metadatos.\n"
    "        self.device = self.declare_parameter(\n"
    "            'device', '/dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0').value\n"
    "        if not os.path.exists(self.device):\n"
    "            self.get_logger().warning(f'{self.device} no existe: uso /dev/video0')\n"
    "            self.device = '/dev/video0'\n")
open(p, 'w').write(s)
