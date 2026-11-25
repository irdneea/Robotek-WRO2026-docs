"""Aplica 'reabrir la camara tras una desconexion' a peripherals/camera_publisher.py (despues de by-id).

  python3 patch_camera_publisher_reopen.py ~/wro_controller_ws/src/peripherals/peripherals/camera_publisher.py

Si la camara USB se desconecta, el kernel la reenumera (otro /dev/videoN) y el descriptor abierto queda
muerto: cap.read() falla para siempre (el 9 oct 2026: 365 'Fallo al capturar cuadro' hasta reiniciar).
Con el parche, tras `reopen_after` fallos seguidos (30 por defecto; 0 = desactivado) el nodo libera el
descriptor y reabre la ruta estable (by-id), reintentando cada `reopen_retry` s (1,0) hasta que aparezca."""
import sys
p = sys.argv[1]
s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


if '\nimport time\n' not in s:
    rep("\nimport os\n", "\nimport os\nimport time\n")
rep("        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)\n"
    "        if not self.cap.isOpened():\n"
    "            self.get_logger().error(f'No se pudo abrir la camara {self.device}')\n",
    "        # Si la camara se desconecta el descriptor abierto queda muerto: tras reopen_after fallos\n"
    "        # seguidos se reabre sola, reintentando cada reopen_retry s (0 = desactivado).\n"
    "        self.reopen_after = int(self.declare_parameter('reopen_after', 30).value)\n"
    "        self.reopen_retry = float(self.declare_parameter('reopen_retry', 1.0).value)\n"
    "        self._ultimo_reintento = 0.0\n"
    "\n"
    "        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)\n"
    "        if not self.cap.isOpened():\n"
    "            self.get_logger().error(f'No se pudo abrir la camara {self.device}')\n")
rep("    def _publicar(self):\n",
    "    def _reabrir(self):\n"
    "        \"\"\"Libera el descriptor muerto y reabre la camara por su ruta estable (by-id).\"\"\"\n"
    "        ahora = time.monotonic()\n"
    "        if ahora - self._ultimo_reintento < self.reopen_retry:\n"
    "            return\n"
    "        self._ultimo_reintento = ahora\n"
    "        self.cap.release()\n"
    "        if not os.path.exists(self.device):\n"
    "            self.get_logger().warn(\n"
    "                f'Reabrir: {self.device} aun no existe, reintento en {self.reopen_retry:g} s')\n"
    "            return\n"
    "        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)\n"
    "        if not self.cap.isOpened():\n"
    "            self.get_logger().warn(\n"
    "                f'Reabrir: no se pudo abrir {self.device}, reintento en {self.reopen_retry:g} s')\n"
    "            return\n"
    "        self._configurar_captura()\n"
    "        self._configurar_imagen()\n"
    "        self.get_logger().info(\n"
    "            f'Camara {self.device} reabierta tras {self._fallos} fallos seguidos')\n"
    "\n"
    "    def _publicar(self):\n")
rep("            self._fallos += 1\n            return\n",
    "            self._fallos += 1\n"
    "            if self.reopen_after > 0 and self._fallos >= self.reopen_after:\n"
    "                self._reabrir()\n"
    "            return\n")
open(p, 'w').write(s)
