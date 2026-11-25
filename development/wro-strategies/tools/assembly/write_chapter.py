#!/usr/bin/env python3
"""Write the «Armar y conectar el coche» chapter of the Open guide (Portfolio-Astro).

    python3 tools/assembly/write_chapter.py ~/Projects/Portfolio-Astro

Images: public/learn/assembly/ (tools/assembly/render.html + save_server.py, wiring_svg.py).
"""
import sys
from pathlib import Path

A = '/learn/assembly/'
TEAM = 'https://github.com/strvaeq/Robotek-WRO2026'


def parts(items):
    out = []
    for image, count, name in items:
        img = f'<img src="{A}part-{image}.png" alt="{name}" loading="lazy">' if image else ''
        out.append(f'<figure>{img}<figcaption><b>{count}x</b>{name}</figcaption></figure>')
    return '<div class="lego-parts">' + ''.join(out) + '</div>'


def step(number, items, view, note, alt):
    return (f'<div class="lego-step">\n<div><div class="lego-num">{number}</div>\n{parts(items)}</div>\n'
            f'<img class="lego-view" src="{A}{view}" alt="{alt}" loading="lazy">\n'
            f'<p class="lego-note">{note}</p>\n</div>\n')


FRONT = '''---
guide: "open-strategy"
order: 9.5
slug: "armar-y-conectar-el-coche"
title: "Armar y conectar el coche"
summary: "Las instrucciones de montaje del coche del equipo, paso a paso y con dibujos de sus piezas, y cómo conectar cada cable."
tag: "step-9"
compareFrom: "step-9"
---

Antes de llevar tu nodo al coche real ([el capítulo siguiente](/learn/open-strategy/paso-10-el-coche-real/)) hay que armarlo y cablearlo. Estas instrucciones siguen el orden del README del equipo Robotek ([Robotek-WRO2026]({team}), sección *Assembly Instructions*) y su diagrama de cables, con dibujos hechos a partir del modelo 3D del coche que usa la simulación: las mismas piezas (`robotek_description/meshes`, sacadas del `Assembly3.stp` del 20 y 21 de octubre de 2026) en el mismo sitio que en el URDF.

> **Qué es exacto y qué es aproximado.** La placa base, la caja, el soporte y la cámara, el servo, la Raspberry Pi, la placa del driver, el LiDAR LD19, la placa RRC Lite y todos los tornillos y tuercas son las piezas del modelo 3D del equipo (`Assembly3.stp`, abierto en SolidCraft), en su sitio; en ese modelo la RRC Lite tiene la forma de una Raspberry Pi. Las ruedas salen de las medidas del URDF (`vehicle.py`). El motor, el eje y las piezas de la dirección **no están en el modelo**: los dibujé con formas simples donde los describe el README del equipo, así que su forma y su posición son aproximadas. Ante cualquier duda, manda el coche real y las fotos del equipo ([`v-photos`]({team}/tree/main/v-photos)).

## Lo que necesitas

| Pieza | Cantidad | Para qué |
|---|---:|---|
| Placa base y piezas impresas en 3D (caja, soporte de cámara, ruedas) | 1 juego | El chasis; los STL están en [`models`]({team}/tree/main/models) |
| Raspberry Pi 5 | 1 | El cerebro: corre ROS 2 y tu nodo |
| Placa RRC Lite | 1 | IMU, servo, motor, botón, medida de batería; da los 5 V del Pi |
| LiDAR LD19 (STL-19P) con su adaptador USB | 1 | Distancias en ±110° hacia delante |
| Cámara USB (icSpring) | 1 | Color de las líneas y de las señales |
| Servo digital de 15 kg·cm | 1 | La dirección |
| Motor 310 con reductora 1:90 y encoder | 1 | La tracción trasera, en el puerto M1 de la RRC Lite (desde el 1 nov 2026; antes, un motor de 25 mm con un puente TB6612) |
| Batería | 1 | La RRC Lite, que da 5 V al Pi y mueve el servo y el motor |
| Anillo de 16 LED WS2812 | 1 | Luz para ver mejor los colores |
| Protectores de rueda de maleta | 4 | Los neumáticos de las ruedas impresas |
| Cables USB (3), USB-C (1), dupont hembra-hembra (3, los LED) | | Las conexiones |
| Tornillos M2×10 (7) y M2×14 (1), tuercas M2 (8) | | La Raspberry Pi y la RRC Lite a la caja |
| Tornillos PA2×6 (4) | | El LiDAR |
| Tornillos M1.6×16 (2) y tuercas M1.6 (2) | | La cámara a su soporte |

Herramientas: destornilladores pequeños, llave para las tuercas del kit y, si vas a cambiar cables, un tester.

## Bolsa 1: el chasis

'''.replace('{team}', TEAM)

MIDDLE = '''
## Bolsa 2: la electrónica y los sensores

'''

CABLES = '''
## Bolsa 3: los cables

Con todo montado, conecta los cables **con la batería desenchufada**. Va a la RRC Lite, que alimenta el Pi, el servo y el motor. Los colores de los dibujos son los de los esquemas, no tienen que coincidir con los de tus cables; lo que importa es cada extremo.

<img class="lego-wiring" src="{A}wiring-usb.svg" alt="Paso 11: cámara, LiDAR y placa RRC Lite por USB a la Raspberry Pi 5" loading="lazy">

<img class="lego-wiring" src="{A}wiring-motor.svg" alt="Paso 12: el motor 310 al puerto M1 de la placa RRC Lite y el servo al conector J4 (canal PWM 1)" loading="lazy">

<img class="lego-wiring" src="{A}wiring-power.svg" alt="Paso 13: la batería a la RRC Lite, que da 5 V al Pi por USB-C; el anillo de LED al GPIO10" loading="lazy">

| Cable | De | A | Ojo con |
|---|---|---|---|
| USB | Cámara | Pi, USB 0 azul | el nodo de la cámara muere si la conectas con todo en marcha: relánzalo |
| USB | Adaptador del LiDAR | Pi, USB 0 negro | 230 400 baudios; `/dev/serial/by-id/usb-Silicon_Labs_CP2102_…` |
| USB | RRC Lite | Pi, USB 1 negro | `/dev/serial/by-id/usb-1a86_USB_Single_Serial_…` |
| 3 hilos | Servo | RRC Lite, conector J4 | es el canal PWM 1 (`acker_channel: 1`, medido el 1 nov 2026) |
| cable del motor | Motor 310 (motor y encoder) | RRC Lite, puerto M1 | `rrc_motor_port: 1`; con +rps el coche va hacia atrás (`rrc_motor_sign: -1`) |
| batería | Batería | RRC Lite, entrada de batería | la placa se apaga bajo 6 V |
| USB-C | RRC Lite (5 V, 5 A) | Pi, entrada USB-C | es la alimentación del Pi |
| dupont | Pi 5 V, GND y GPIO10 (pin 19) | anillo de LED: 5 V, GND y DIN | brillo bajo: al 100 % reinició el Pi |

## Paso 14: comprobar antes de rodar

<div class="lego-step">
<div><div class="lego-num">14</div>
<div class="lego-parts"><figure><img src="{A}final-back.png" alt="El coche armado, visto desde atrás" loading="lazy"><figcaption><b>1x</b>coche armado</figcaption></figure></div></div>
<img class="lego-view" src="{A}final.png" alt="El coche armado: placa, ruedas, servo, caja, Raspberry Pi, LiDAR y cámara" loading="lazy">
<p class="lego-note">Con el coche en alto (las ruedas sin tocar el suelo), enchufa la batería y espera a que arranque el Pi. Comprueba, en este orden y como explica el <a href="/learn/open-strategy/paso-10-el-coche-real/">capítulo siguiente</a> (sección 3): que se ven los tres USB, la cámara, el LiDAR (unos 10 Hz), la IMU (unos 49 Hz), el centro y el signo de la dirección y, por último, el motor a poca velocidad.</p>
</div>

## Si algo falla

- **El motor no gira y el servo sí.** Revisa el cable del motor en M1 y que `rrc_motor_port` de `robot.yaml` sea ese puerto. Con el motor 310 nuevo, a menos de unos 2 rps de la placa las ruedas giran en el aire pero no mueven el coche en el suelo.
- **El motor está muy caliente.** Pasa si se queda frenado empujando (un choque de frente quemó el motor anterior): apágalo y no subas el tope `motor_max_rps` sin necesidad.
- **El Pi se reinicia.** Revisa cada conector (al equipo le pasó con un cable flojo) y baja el brillo de los LED.
- **Falta un dispositivo en `/dev/serial/by-id`.** Es el cable o el adaptador; los nombres no dependen del puerto.
- **Las ruedas delanteras no vuelven al centro o rozan.** Revisa que las piezas móviles de la dirección giren libres y que la bieleta corta vaya al lado contrario del eje del servo.

## Resumen

- Tres bolsas: el chasis (placa, dirección, motor, ruedas), la electrónica y los sensores (driver, caja, Pi, RRC Lite, LiDAR, cámara, con sus tornillos) y los cables (USB, motor y servo, energía y luces).
- Los sensores y la RRC Lite van por USB al Pi; el motor, al puerto M1 de la RRC Lite, y el servo, a su conector J4 (canal 1).
- Una batería, a la RRC Lite, que mueve el motor y el servo y da 5 V al Pi por USB-C.
- Las piezas dibujadas salen del modelo 3D del equipo (el mismo de la simulación, más los tornillos, el LD19 y la RRC Lite de SolidCraft); el motor y la dirección, de la descripción del equipo.
'''.replace('{A}', A)


def main():
    root = Path(sys.argv[1]).expanduser()
    s = []
    s.append(step(1, [('plate', 1, 'placa base')], 'step-1.png',
                  'La placa base del kit (la del modelo del equipo). La pestaña de delante, más baja, es donde irá el LiDAR; los agujeros de los ejes marcan la distancia entre ejes de 117,4 mm.',
                  'Paso 1: la placa base sola'))
    s.append(step(2, [('servo', 1, 'servo'), ('ackermann', 1, 'dirección Ackermann')], 'step-2.png',
                  'Atornilla las piezas fijas de la dirección a la placa y, a sus lados, las dos piezas móviles que giran las ruedas: deben girar libres, y se usa el agujero más cercano a la rueda. Únelas con la barra de dirección (con rodamientos en los extremos). Una bieleta más corta va de una de esas piezas al servo, que se monta <b>vertical</b> en la placa; el eje del servo y el lado de la bieleta quedan en lados opuestos.',
                  'Paso 2: el servo baja hasta su hueco en la placa; la dirección se monta delante'))
    s.append(step(3, [('motor', 1, 'motor'), ('axle', 1, 'eje trasero')], 'step-3.png',
                  'Atornilla el soporte del motor a la placa y el motor al soporte. El eje pasa por las dos aberturas del soporte, sobre dos rodamientos que lo centran y dos anillos que lo frenan de lado. Une el eje del motor y el eje trasero con separadores, sin que choquen con los tornillos del motor.',
                  'Paso 3: el eje entra de lado y el motor por detrás (posiciones aproximadas)'))
    s.append(step(4, [('wheelFL', 4, 'rueda')], 'step-4.png',
                  'Las cuatro ruedas impresas, con un protector de rueda de maleta como neumático (61 mm de diámetro, 14,5 mm de ancho). Las delanteras van en los bujes de la dirección, con rodamientos que las dejen girar libres; las traseras, en el eje. Vía: 133,5 mm delante y 123,5 mm detrás.',
                  'Paso 4: las cuatro ruedas entran por los lados'))
    s.append(MIDDLE)
    s.append(step(5, [('driver', 1, 'placa del driver')], 'step-5.png',
                  'La placa del driver va en la parte trasera de la placa base (en el modelo del equipo se llama <code>driver_board</code>).',
                  'Paso 5: la placa del driver baja a la parte trasera'))
    s.append(step(6, [('case', 1, 'caja impresa')], 'step-6.png',
                  'La caja impresa va encima de la placa y forma un techo sobre el servo, que asoma por arriba de la base.',
                  'Paso 6: la caja impresa baja sobre la placa'))
    s.append(step(7, [('pi', 1, 'Raspberry Pi 5'), ('m2x10', 4, 'tornillo M2×10'), ('nutM2', 4, 'tuerca M2')], 'step-7.png',
                  'La Raspberry Pi 5 va <b>de canto</b>, en el lado izquierdo de la caja: cuatro tornillos M2×10 desde fuera y sus tuercas por dentro. Así montada, los ejes de la IMU no coinciden con los del coche: el capítulo siguiente explica cómo medirlos con <code>imu_axes</code>.',
                  'Paso 7: la Raspberry Pi entra de lado en la caja con cuatro tornillos M2'))
    s.append(step(8, [('rrc', 1, 'placa RRC Lite'), ('m2x10', 3, 'tornillo M2×10'), ('m2x14', 1, 'tornillo M2×14'), ('nutM2', 4, 'tuerca M2')], 'step-8.png',
                  'La placa RRC Lite va de canto en el otro lado de la caja (el derecho), con tres tornillos M2×10, uno M2×14 y cuatro tuercas M2. Es la que lleva la IMU: si la cambias de lado, cambian los ejes.',
                  'Paso 8: la RRC Lite entra de lado por la derecha de la caja con cuatro tornillos M2'))
    s.append(step(9, [('lidar', 1, 'LiDAR LD19'), ('pa2x6', 4, 'tornillo PA2×6')], 'step-9.png',
                  'El LiDAR va delante, en la pestaña de la placa, sujeto desde abajo con cuatro tornillos PA2×6 y con la vista despejada: mira 110° a cada lado. Su plano de medida queda a 30 mm del suelo y 128 mm por delante del centro del coche (<code>base_link</code>).',
                  'Paso 9: el LiDAR baja a la pestaña delantera y cuatro tornillos suben desde abajo'))
    s.append(step(10, [('camSupport', 1, 'soporte de la cámara'), ('camera', 1, 'cámara'), ('m16x16', 2, 'tornillo M1.6×16'), ('nutM16', 2, 'tuerca M1.6')], 'step-10.png',
                  'El soporte de la cámara va justo detrás del LiDAR y es más alto, para que la cámara vea por encima; la cámara se sujeta con dos tornillos M1.6×16 y sus tuercas. Medido en el coche: la cámara queda a 144,6 mm del suelo, mirando unos 10° hacia abajo y 4,4° a la izquierda.',
                  'Paso 10: el soporte baja detrás del LiDAR, la cámara encaja arriba con dos tornillos M1.6'))
    s.append(CABLES)
    text = FRONT + '\n'.join(s)
    path = root / 'src/content/learn/steps/open-strategy/armar-y-conectar-el-coche.md'
    path.write_text(text)
    print('wrote', path)


if __name__ == '__main__':
    main()
