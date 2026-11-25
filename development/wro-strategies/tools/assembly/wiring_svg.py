#!/usr/bin/env python3
"""LEGO-style wiring panels of the Robotek car (SVG), from the team's wiring diagram and the
connections measured on the Pi (docs/robot-real-pi.md, docs/robot-real-pi/conexiones-sensores.svg).

    python3 tools/assembly/wiring_svg.py ~/Projects/Portfolio-Astro/public/learn/assembly
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BG, BOX, INK = '#d7ebf6', '#b6d2e4', '#1d2430'
FONT = 'font-family="Helvetica, Arial, sans-serif"'


def text(x, y, s, size=15, weight='normal', anchor='start', fill=INK):
    return (f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}">{escape(s)}</text>')


def part(x, y, w, h, name, sub='', fill='#ffffff', stroke=INK):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>',
           text(x + w / 2, y + 26, name, 17, 'bold', 'middle')]
    if sub:
        for k, line in enumerate(sub.split('\n')):
            out.append(text(x + w / 2, y + 47 + 18 * k, line, 13, anchor='middle'))
    return '\n'.join(out)


def pin(x, y, label, side='left'):
    anchor = 'end' if side == 'left' else 'start'
    dx = -10 if side == 'left' else 10
    return (f'<circle cx="{x}" cy="{y}" r="5.5" fill="#f2c94c" stroke="{INK}" stroke-width="1.5"/>'
            + text(x + dx, y + 5, label, 13, 'bold', anchor))


def cable(points, color, width=6):
    d = 'M ' + ' L '.join(f'{x} {y}' for x, y in points)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width + 3}" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')


def panel(number, title, parts, body, width=1000, height=560):
    """parts: [(count, label)] for the box of pieces, as in the building-block instructions."""
    box_h = 46 + 26 * len(parts)
    items = [f'<rect x="20" y="20" width="300" height="{box_h}" fill="{BOX}" stroke="{INK}" stroke-width="2"/>',
             text(34, 46, 'Necesitas', 15, 'bold')]
    for k, (count, label) in enumerate(parts):
        items.append(text(34, 74 + 26 * k, f'{count}x', 15, 'bold'))
        items.append(text(72, 74 + 26 * k, label, 15))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{escape(title)}">'
            f'<rect width="{width}" height="{height}" fill="{BG}"/>'
            + text(20, height - 24, str(number), 64, 'bold')
            + text(100, height - 36, title, 20, 'bold')
            + '\n'.join(items) + body + '</svg>')


def usb():
    body = [
        part(380, 40, 300, 250, 'Raspberry Pi 5', '2 controladores: azul 3.0, negro 2.0', '#e8f5ec'),
        f'<rect x="420" y="150" width="105" height="120" rx="10" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>',
        f'<rect x="545" y="150" width="105" height="120" rx="10" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>',
        text(430, 262, 'USB 0', 15, 'bold'), text(555, 262, 'USB 1', 15, 'bold'),
        f'<rect x="440" y="190" width="30" height="26" rx="3" fill="#2f6fd6" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="475" y="190" width="30" height="26" rx="3" fill="#222" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="565" y="190" width="30" height="26" rx="3" fill="#2f6fd6" stroke="{INK}" stroke-width="2"/>',
        f'<rect x="600" y="190" width="30" height="26" rx="3" fill="#222" stroke="{INK}" stroke-width="2"/>',
        text(455, 236, 'azul', 12, anchor='middle'), text(490, 236, 'negro', 12, anchor='middle'),
        text(580, 184, 'azul', 12, anchor='middle'), text(615, 184, 'negro', 12, anchor='middle'),
        part(760, 40, 220, 80, 'Cámara', 'USB 2.0 · /dev/video0'),
        part(760, 160, 220, 80, 'LiDAR LD19', 'con su adaptador USB (CP2102)'),
        part(760, 290, 220, 80, 'Placa RRC Lite', 'USB · /dev/ttyACM0'),
        cable([(760, 80), (700, 80), (700, 122), (455, 122), (455, 190)], '#9b59b6'),
        cable([(760, 200), (730, 200), (730, 140), (490, 140), (490, 190)], '#e67e22'),
        cable([(760, 330), (690, 330), (690, 300), (615, 300), (615, 216)], '#27ae60'),
        text(30, 420, 'Así quedó medido en el coche del equipo: cámara al azul del USB 0, LiDAR al negro del USB 0', 14, 'bold'),
        text(30, 442, 'y placa al negro del USB 1. Los tres son USB 2.0 o 1.1, así que cualquier puerto sirve, y los', 14),
        text(30, 464, 'nombres /dev/serial/by-id no dependen del puerto. Enchúfalos con el Pi apagado.', 14),
    ]
    return panel(11, 'Los sensores, por USB', [(3, 'cable USB'), (1, 'adaptador USB del LiDAR')], '\n'.join(body), height=580)


PIN_TYPE = {1: '3v3', 17: '3v3', 2: '5v', 4: '5v', 6: 'gnd', 9: 'gnd', 14: 'gnd', 20: 'gnd', 25: 'gnd',
            30: 'gnd', 34: 'gnd', 39: 'gnd'}
def motor():
    """Since 1 nov 2026: the 310 encoder motor on port M1 of the RRC Lite and the servo on J4 (PWM channel 1)."""
    ports = {name: 150 + 70 * k for k, name in enumerate(('M1', 'M2', 'M3', 'M4'))}
    body = [
        part(380, 90, 280, 420, 'Placa RRC Lite', 'puertos de motor con encoder\ny de servo PWM', '#e8f5ec'),
    ]
    for name, y in ports.items():
        body.append(pin(660, y, name, 'left'))
    body += [
        pin(380, 440, 'J4 · canal PWM 1', 'right'),
        cable([(660, ports['M1']), (740, ports['M1'])], '#c0392b', 6),
        part(740, 100, 240, 110, 'Motor 310', 'reductora 1:90, encoder Hall\ncable de motor y encoder'),
        cable([(380, 440), (320, 440), (320, 500)], '#8e44ad', 5),
        part(30, 500, 290, 90, 'Servo de dirección', 'al conector J4 de la RRC Lite\n(canal PWM 1)'),
        text(30, 180, 'El motor va al puerto M1.', 14, 'bold'), text(30, 200, 'La placa mantiene la velocidad', 14),
        text(30, 220, 'con el encoder (en rps).', 14),
        text(30, 252, 'Puerto en robot.yaml:', 14, 'bold'), text(30, 272, 'rrc_motor_port: 1 y', 14),
        text(30, 292, 'rrc_motor_sign: -1 (con +rps', 14), text(30, 312, 'el coche va hacia atrás).', 14),
        text(30, 344, 'El servo va a J4, que es el', 14, 'bold'), text(30, 364, 'canal 1 (acker_channel: 1).', 14),
        text(30, 396, 'Sin cables al Pi: todo va por', 14), text(30, 416, 'la RRC Lite (USB, paso 11).', 14),
    ]
    return panel(12, 'Motor y dirección', [(1, 'motor 310 con su cable'), (1, 'servo con su cable de 3 hilos')],
                 '\n'.join(body), height=700)


def power():
    body = [
        part(380, 40, 240, 110, 'Batería', 'a la RRC Lite\n(su entrada admite 6 a 14 V)', '#fdecea'),
        part(380, 230, 240, 130, 'Placa RRC Lite', 'mueve el motor y el servo\nsalida 5 V / 5 A\n(USB-C, PD)'),
        part(720, 230, 250, 110, 'Raspberry Pi 5', 'entrada USB-C', '#e8f5ec'),
        part(720, 420, 250, 110, 'Anillo de 16 LED', 'WS2812: 5 V, GND y DIN\nDIN al GPIO10 (pin 19)'),
        cable([(500, 150), (500, 230)], '#c0392b', 7),
        cable([(620, 285), (720, 285)], '#2c3e50', 7),
        cable([(845, 340), (845, 420)], '#27ae60', 4),
        text(30, 380, 'Una batería, a la RRC Lite: da', 14, 'bold'), text(30, 400, 'el motor (M1), el servo y los', 14, 'bold'),
        text(30, 420, '5 V del Pi por USB-C.', 14),
        text(30, 452, 'La RRC Lite se apaga bajo 6 V:', 14), text(30, 472, 'cárgala antes de cada ronda.', 14),
        text(30, 504, 'LED con brillo bajo.', 14),
    ]
    return panel(13, 'Energía y luces', [(1, 'batería con su conector'), (1, 'cable USB-C a USB-C'),
                                         (3, 'cable dupont para los LED')], '\n'.join(body), height=620)


def main():
    out = Path(sys.argv[1]).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    for name, build in (('wiring-usb', usb), ('wiring-motor', motor), ('wiring-power', power)):
        (out / f'{name}.svg').write_text(build())
        print('wrote', name)


if __name__ == '__main__':
    main()
