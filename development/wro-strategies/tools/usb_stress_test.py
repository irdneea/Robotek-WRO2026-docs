#!/usr/bin/env python3
"""Prueba de estrés de los USB del coche: huecos en la IMU/batería (placa), el LiDAR y la cámara.

Corre en el Pi con el stack de sensores en marcha (nodo de la placa, LiDAR y cámara), p. ej.:
  ssh user@192.168.0.10 'source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=1; python3 - --seconds 120' < tools/usb_stress_test.py

Mide, por cada tópico, la frecuencia y los HUECOS entre mensajes (el síntoma de un timeout o de una
placa que se queda sin responder), y lee el log del kernel (journalctl -k) buscando errores USB
durante la prueba (reset, disconnect, error, timeout, overcurrent). Solo lectura: no manda órdenes.
Un veredicto PASS necesita: frecuencia >= 90 % de la nominal, ningún hueco > max_gap y ningún error
USB nuevo en el kernel. No prueba la causa de un fallo: solo dice si ocurre."""
import argparse
import re
import subprocess
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Imu, LaserScan
from std_msgs.msg import UInt16

# tópico, tipo, frecuencia nominal (Hz), hueco máximo tolerado (s)
TOPICS = [
    ('/rrc/imu_raw', Imu, 49., .10),
    ('/rrc/battery', UInt16, .5, 4.5),
    ('/scan', LaserScan, 10., .30),
    ('/usb_cam/image_raw', Image, 12., .60),
]
USB_ERROR = re.compile(r'(usb|xhci|cdc_acm|cp210x|uvc).*(error|reset|disconnect|timeout|overcurrent|fail|-71|-110)',
                       re.IGNORECASE)


def kernel_lines():
    out = subprocess.run(['journalctl', '-k', '--no-pager', '-o', 'short-monotonic'],
                         capture_output=True, text=True, timeout=20).stdout
    return out.splitlines()


class Stress(Node):
    def __init__(self):
        super().__init__('usb_stress')
        self.t = {name: [] for name, *_ in TOPICS}
        for name, kind, *_ in TOPICS:
            self.create_subscription(kind, name, lambda m, n=name: self.t[n].append(time.monotonic()),
                                     qos_profile_sensor_data)


def report(times, nominal, max_gap, seconds):
    if len(times) < 2:
        return 'FAIL', f'{len(times)} mensajes (sin datos)'
    gaps = [b-a for a, b in zip(times, times[1:])]
    rate = (len(times)-1)/(times[-1]-times[0])
    start_gap = times[0]
    big = [g for g in gaps if g > max_gap]
    ok = rate >= .9*nominal and not big
    text = (f'{len(times):5d} msgs  {rate:6.2f} Hz (nominal {nominal:g})  hueco máx {max(gaps):.3f} s  '
            f'huecos > {max_gap:g} s: {len(big)}  primer mensaje a {start_gap:.1f} s')
    return ('PASS' if ok else 'FAIL'), text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=120.)
    ap.add_argument('--warmup', type=float, default=8., help='segundos iniciales que no cuentan')
    args = ap.parse_args()
    before = kernel_lines()
    rclpy.init()
    node = Stress()
    t0 = time.monotonic()
    while time.monotonic()-t0 < args.seconds+args.warmup:
        rclpy.spin_once(node, timeout_sec=.05)
    cut = t0+args.warmup
    print(f'== {args.seconds:.0f} s de medida (tras {args.warmup:.0f} s de calentamiento)')
    worst = 'PASS'
    for name, _, nominal, max_gap in TOPICS:
        times = [x-cut for x in node.t[name] if x >= cut]
        status, text = report(times, nominal, max_gap, args.seconds)
        worst = 'FAIL' if status == 'FAIL' else worst
        print(f'{status:4}  {name:34}{text}')
    new = [l for l in kernel_lines()[len(before):] if USB_ERROR.search(l)]
    print(f'== log del kernel: {len(new)} líneas nuevas con errores USB')
    for line in new[:10]:
        print('   ', line[:160])
    if new:
        worst = 'FAIL'
    load = open('/proc/loadavg').read().split()[:3]
    print('== carga', ' '.join(load), '| throttled', subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True,
                                                                   text=True).stdout.strip())
    print('RESULTADO:', worst)
    node.destroy_node()
    rclpy.shutdown()


main()
