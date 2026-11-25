# Raspberry Pi del coche: acceso, sensores en RViz y detector de pilares

> **Nombres nuevos (9 oct 2026):** el driver de la placa es `rrc_lite_driver` (antes
> `ros_robot_controller`), con mensajes `rrc_lite_msgs`, nodo `rrc_driver` y tópicos `/rrc/…`. Este
> documento ya usa los nombres nuevos, también al contar pruebas anteriores, que se hicieron con
> los viejos: [nombres nuevos](robot-real-pi/rename/README.md).

7 de octubre de 2026. Primera sesión trabajando en el Pi del coche por SSH. Todo lo hecho
se probó **con el coche quieto**: el motor no se usó en ningún momento. Los archivos que
solo viven en el Pi están copiados en [robot-real-pi/](robot-real-pi/).

## Flujo: push en el Mac, pull en el Pi

Desde el 9 oct 2026 **el coche corre solo con este repo**: trae el driver de la placa
(`rrc_lite_driver`, `rrc_lite_msgs`), `peripherals` (cámara, `sensors.launch.py`, tira LED) y el
LiDAR (`ldlidar_stl_ros2`), además de `robotek_*`. Ya no se copia nada con `rsync`.

En el Mac, después de cambiar el código:

```bash
git push
```

En el Pi, `~/Projects/WRO-Strategies` es un **clon superficial** de GitHub, hecho una vez con
`git clone --depth 1 https://github.com/coach/WRO-Strategies.git` (solo baja la versión
actual: 38 MB, frente a los 210 MB del historial completo, que por la Wi‑Fi del coche tarda más de
15 min). `gh` ya está autenticado con la cuenta del repo. Para actualizar:

```bash
cd ~/Projects/WRO-Strategies && git pull && colcon build
```

`colcon build` en el Pi compila los 12 paquetes: ~12 s desde la segunda vez (la primera tarda
~55 s, casi todo generando `rrc_lite_msgs`). La simulación solo suma ~2 s, así que no se salta.

Cada terminal del Pi carga ROS y el repo (bloque `# >>> robotek workspace >>>` de `~/.bashrc`):
`source /opt/ros/jazzy/setup.bash` y `source ~/Projects/WRO-Strategies/install/setup.bash`. **No
cargar `~/wro_controller_ws`**: tiene los mismos paquetes (copia antigua) y se mezclarían. La copia
de `rsync` anterior quedó en `~/Projects/WRO-Strategies-rsync-20261009`.

Reglas:

- Los cambios se hacen **en el Mac** y se suben. Si hay que tocar algo en el Pi para probar, hacer
  commit desde el Pi (`git commit` y `git push`) o copiar el cambio al Mac. Si no, el siguiente
  `git pull` choca o se pierde.
- Lo generado en el Pi (`build/`, `install/`, `log/`, `~/robotek-runs/`) no va a git.
- La IP del Pi puede cambiar (DHCP): comprobarla con el router o con
  `ssh -o HostKeyAlias=192.168.0.10 user@<ip>`.

## Acceso

```bash
ssh user@192.168.0.10        # llave ed25519 de la Mac instalada con ssh-copy-id
export ROS_DOMAIN_ID=1           # el del equipo (scripts/ros_autostart.sh); igual en la Mac
```

## Qué hay en el Pi

El nodo de la placa (`rrc_driver`) es un fork del oficial de Hiwonder: lo que publica y recibe
el original, y qué comparar con el Pi, en [ros-robot-controller-oficial.md](ros-robot-controller-oficial.md).

| Cosa | Detalle |
|---|---|
| Sistema | Raspberry Pi (`user-desktop`), Ubuntu 24.04.5, kernel `6.8.0-*-raspi`, ROS 2 Jazzy, 4 núcleos, 7,7 GB RAM |
| Disco | 57 GB. Estaba al 96 %; se borró `~/kernel-build` (20 GB, fuentes de un kernel compilado en jul. 2025 que no se usa) → 61 %. Otros candidatos (requieren `sudo`): `apt clean`, snaps viejos (3 GB), 11 kernels instalados, journal (700 MB) |
| Workspace del equipo | `~/wro_controller_ws`: `rrc_lite_driver` (placa, `acker_lidar_node`, `camara`, `motor`, `led`), `peripherals`, `ldlidar_stl_ros2` |
| Código del equipo | `~/Documents/Testv1` (Open: `open/run_open.sh`; muchas variantes) |
| Nuestra repo | `~/Projects/WRO-Strategies` (copiada con `rsync`, sin `git clone`); `colcon build` OK (8 paquetes, 14 s) |
| Arranque automático | **Desactivado el 9 oct 2026** (`systemctl --user disable --now ros_autostart.service`): el stack ya no arranca al encender. La lógica (modo `~/.config/wro_mode`, `ros_autostart.sh`) sigue en el Pi y copiada en [robot-real-pi/autostart/](robot-real-pi/autostart/README.md), con cómo reactivarla |
| Detenerlo | `~/scripts/stop_ros.sh` (para el servicio y mata el stack; **no** mata nodos lanzados a mano como `camera_publisher`) |

**Ojo:** con `wro.launch.py` corriendo están `acker_node` y `motor`: el coche puede arrancar.
Nuestros launches usan los mismos puertos (LiDAR, placa): detener primero el stack del equipo.

### Dispositivos y tópicos

| Sensor | Dispositivo | Tópico | Notas |
|---|---|---|---|
| LiDAR | `/dev/ttyUSB0` (CP2102), 230400 baud | `/scan`, frame `lidar_frame`, ~10 Hz | Driver configurado como **LD19** (no STL-19P). Ángulos 0…2π, **frente en π**, antihorario (como `acker_lidar_node`: frente 180°, izq. 240°, der. 120°) → `scan_adapter` con `angle_offset: π`, `reverse: false` es correcto. **Ve ±110°**: detrás los rayos dan en el propio coche a 2–8 cm (`scan_adapter` los descarta: `fov_deg` 110, `min_valid_range` 0,12) |
| Placa RRC Lite | `/dev/ttyACM0` (USB `1a86:55d4` «USB Single Serial», driver `cdc_acm`; no es un CH340) | `/rrc/imu_raw` (~49 Hz), `battery` (mV), `button`, servo en `acker_servo/set_state` | No existe `rrc_lite_driver.launch.py`: es `ros2 run rrc_lite_driver rrc_driver`. La IMU manda **orientación vacía** (cuaternión 0,0,0,0): solo giroscopio y acelerómetro |
| Cámara | `/dev/video0` (usar `/dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0`), USB `icSpring camera` (32e6:9005), solo YUYV 640×480 | `/usb_cam/image_raw` (~6 fps reales) | Nodo `peripherals camera_publisher` (no `usb_cam`). Si la cámara se conecta después de arrancar, el nodo muere: relanzarlo |
| Tira LED | WS2812, SPI0 (`/dev/spidev0.0`, pin 19 / GPIO10), librería `rpi5_ws2812` | — | `led_node` del equipo la pone en blanco 100 % al arrancar (`led_ros.py`; en esa versión ambos comandos ponen blanco). Prueba: `~/neopixel.py` |

## Los USB y sus nombres estables (9 oct 2026)

Inventario del Pi (`lsusb`, `udevadm`), con los tres dispositivos conectados:

| Dispositivo | USB | Nodo | Nombre estable (por id de USB, no depende del puerto) |
|---|---|---|---|
| Placa RRC Lite | `1a86:55d4` «USB Single Serial», serie `586B015678`, `cdc_acm` | `/dev/ttyACM0` | `/dev/serial/by-id/usb-1a86_USB_Single_Serial_586B015678-if00` |
| LiDAR LD19 | `10c4:ea60` CP2102, serie `0001`, `cp210x` | `/dev/ttyUSB0` | `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0` |
| Cámara | `32e6:9005` icSpring, `uvcvideo`, sin número de serie | `/dev/video0` (captura) y `/dev/video1` (metadatos) | `/dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0` |

- **El código del equipo ya usaba el nombre estable** para la placa (`rrc_driver.py`, con el
  motivo en un comentario) y para el LiDAR (`ldlidar_LD19.launch.py`). Esos dos funcionan en
  cualquier puerto. No existe `/dev/rrc`: la regla `99-ttyACM0.rules` está en el repo pero no
  instalada en `/etc/udev/rules.d`, y no hace falta.
- **La cámara era la que faltaba:** `camera_publisher` abría `/dev/video0`, y la Pi 5 tiene unos 19
  nodos de video propios (`video19`–`video37`: codec y `pisp_be`), así que el número de la cámara
  puede cambiar con el orden de arranque. Ahora abre el nombre estable (cambio en la tabla de
  arriba). `robot.launch.py` también (`video_device`).
- **Límites:** el nombre de la placa lleva su número de serie: **si se cambia la placa, hay que
  actualizar la ruta** en `rrc_driver.py`. El LiDAR tiene el serie genérico `0001` de los
  CP2102: dos LiDAR iguales se confundirían. La cámara no tiene serie: dos cámaras iguales también.
- **Puertos:** la placa y la cámara cuelgan del mismo controlador USB (`xhci-hcd.0`, bus 2) y el
  LiDAR del otro (`xhci-hcd.1`, bus 4); la cámara y la placa son USB 2. Mientras los nombres sean
  estables, el puerto físico solo afecta al ancho de banda y a la corriente.
- **Qué conectar dónde (USB 3.0 / 2.0, controladores, alimentación y GPIO):** [reporte en SVG](robot-real-pi/conexiones-sensores.svg).
  Los tres sensores son USB 2.0 o 1.1, así que ningún puerto azul (3.0) les da ventaja. Corriente: fuente
  negociada de 5 A, límite de USB de 1,6 A en total y consumo declarado de 100 + 100 + 136 mA.
- **Segunda prueba (9 oct 2026): LiDAR en un puerto 2.0 (ya estaba ahí), placa y cámara movidas a puertos 3.0.** Mapa con
  `tools/pi_usb_map.sh`: cámara en `xhci-hcd.0` (bus 2, puerto 1), LiDAR en `xhci-hcd.0` (bus 2,
  puerto 2) y placa en `xhci-hcd.1` (bus 4, puerto 1); aunque están en puertos azules, siguen a
  480/12 Mbit/s porque son USB 2.0/1.1. Los nombres `by-id` siguieron a cada uno (LiDAR otra vez
  `ttyUSB0`, cámara `video0`). Con `sensors.launch.py`: `/scan` 10 Hz, `/usb_cam/image_raw` 12,4
  fps, `imu_raw` 49 Hz, sin errores. La cámara dio 15,7 fps en la otra posición: no se puede
  atribuir la diferencia al puerto (la exposición automática y la carga de la medida también cuentan).
  Deducción: en cada controlador el puerto raíz 1 es el azul (3.0) y el 2 el negro (2.0).
- **Tercera prueba (9 oct 2026): la placa en un puerto 2.0, solo la cámara en un 3.0.** Mapa: cámara
  `xhci-hcd.0` puerto 1 (azul), LiDAR `xhci-hcd.0` puerto 2 (negro), placa `xhci-hcd.1` puerto 2
  (negro): confirma que en cada controlador el puerto raíz 1 es el azul y el 2 el negro. La placa es
  un dispositivo USB 1.1 (12 Mbit/s): un puerto 3.0 no le da nada, porque usa el mismo par USB 2.0.
  **Prueba de estrés** ([`tools/usb_stress_test.py`](../tools/usb_stress_test.py), solo lectura):
  placa, LiDAR y cámara (a 30 fps) arrancados **a la vez y sin esperas** (el caso del timeout del
  LiDAR de las notas: sin timeout), 120 s en reposo y 60 s con los 4 núcleos al 100 %:

  | | Reposo (120 s) | CPU al 100 % (60 s) |
  |---|---|---|
  | `imu_raw` (placa) | 48,91 Hz, hueco máx 41 ms, 0 huecos > 100 ms | 48,79 Hz, hueco máx 43 ms, 0 huecos |
  | `battery` | 0,95 Hz, hueco máx 1,07 s | 0,95 Hz, hueco máx 1,07 s |
  | `/scan` (LiDAR) | 9,87 Hz, hueco máx 0,20 s | 9,88 Hz, hueco máx 0,20 s |
  | `/usb_cam/image_raw` | 9,0 Hz, hueco máx 0,40 s | **4,6 Hz, hueco máx 4,8 s** |
  | Errores USB en el kernel | 0 | 0 |

  **No se reprodujeron los timeouts**, ni arrancando todo a la vez ni con la CPU saturada. Los
  timeouts de las notas (LiDAR con la placa al arrancar juntos; dos lectores en el mismo puerto
  serie) eran de software, no de velocidad del puerto. La cámara sí se degrada con la CPU saturada
  (`camera_publisher` es Python con OpenCV): es lo que hay que vigilar si la estrategia carga el Pi.
  Sin ROS, el dispositivo entrega unos 6,5 fps con la luz del momento (exposición automática): la
  tasa de la cámara depende de la luz, no del USB. La batería publica a ~1 Hz, no a ~0,5 Hz. La prueba
  no cubre una desconexión en marcha ni la vibración del coche en movimiento.
- **Prueba de cambio de puerto (9 oct 2026, hecha por el usuario con el stack corriendo):** al mover
  el LiDAR y la cámara a otros puertos, el LiDAR pasó de `ttyUSB0` a `ttyUSB1` y la cámara de
  `video0` a `video1`; los enlaces `by-id` siguieron a cada dispositivo. El kernel no reutiliza el
  índice mientras un proceso mantiene abierto el dispositivo desconectado, y esos procesos se
  quedan sin datos (`/scan` y la cámara en silencio, el IMU seguía a 49 Hz porque la placa no se
  movió): **tras mover un dispositivo hay que relanzar el stack**. Relanzado con los nombres
  estables: `/scan` 12 Hz, `/usb_cam/image_raw` 15,7 fps (por `video1`), `imu_raw` 49 Hz.
- Enchufar los tres **antes** de encender; si la cámara se conecta después, el nodo muere y hay que
  relanzarlo.

### La cámara: formatos, fps y por qué baja (9 oct 2026)

- **No hay especificaciones en el repo de Robotek** (`Robotek-WRO2026`): solo «Monocular Camera… para visión o
  streaming», sin modelo, resolución ni fps. La fuente es el propio dispositivo (`v4l2-ctl --list-formats-ext`):
  **solo YUYV 640×480**, a 30, 25, 20, 15, 10 y 5 fps; **no ofrece MJPEG, H.264 ni 60 fps**. Es un dispositivo
  **USB 2.0** (`bcdUSB 2.00`, 100 mA): un puerto 3.0 no le cambia nada (30 fps de YUYV a 640×480 son ~147 Mbit/s,
  caben en los 480 Mbit/s).
- **Medido sin ROS** (`v4l2-ctl --stream-mmap`): con la **exposición automática** (modo de prioridad de
  apertura, `auto_exposure=3`) da **6,7 fps** con la luz del cuarto: el obturador se alarga y baja la tasa. Con
  exposición manual (`exposure_time_absolute` en unidades de 100 µs): 40 ms → 14,3 fps; 20 ms → 22,5; 10 ms →
  22,6; 5 ms → 22,6. **Techo medido: ~22,6 fps** aunque se pida 30 o 25 (con 20 pedidos da 20,6): el
  dispositivo acepta 30 pero no los entrega; no se encontró la causa.
- **Por qué baja a ~9 en el nodo:** la exposición automática (`camera_publisher` arranca con `manual:=false`) y,
  con la CPU saturada, el propio nodo (Python + OpenCV): a 4 núcleos al 100 % cayó a 4,6 fps con huecos de 4,8 s.
- **Con exposición manual** (`-p manual:=true -p exposure_absolute:=150`, 15 ms) y RViz suscrito a `compressed`:
  **17,1 fps**, 231 KB/s (~1,8 Mbit/s), sin fallos. La imagen es más oscura que con la automática: revisar el
  detector de color antes de adoptarlo.
- **Incidente:** a los 90 s de arrancar el nodo el kernel registró `usb 2-1: USB disconnect` y `uvcvideo: Failed to
  resubmit video URB (-19)`: **la cámara se desconectó y reconectó sola** (volvió como `video1`). Causa sin
  determinar (cable o contacto, o reinicio del propio dispositivo). `camera_publisher` **no se recupera**: se queda
  con el descriptor muerto y repite «Fallo al capturar cuadro» (365 veces) hasta que se reinicia. Pendiente: que el
  nodo reabra la cámara tras N fallos seguidos.

## Ver los sensores en RViz desde la Mac (RoboStack)

Funciona por Wi‑Fi con el **mismo RMW, dominio 1 y descubrimiento `SUBNET` en los dos lados** (firewall
de macOS apagado, multicast DDS pasa por la red); `macos_env.sh` NO sirve tal cual (dominio 42,
`LOCALHOST`). Valores por defecto y causas del fallo del 9 oct: [README, «Red entre el Mac y el Pi»](../README.md#red-entre-el-mac-y-el-pi-dds).
Lanzador: `bash tools/macos_rviz_real.sh [config.rviz]`. Solo la cámara: `docs/robot-real-pi/robot_camera.rviz`. Entorno RoboStack Jazzy existente:
`/home/user/Projects/WRO/.mamba/jazzy`; se instalaron `ros-jazzy-rviz-imu-plugin` y
`ros-jazzy-compressed-image-transport`.

```bash
E=/home/user/Projects/WRO/.mamba/jazzy
export PATH=$E/bin:$PATH AMENT_PREFIX_PATH=$E CMAKE_PREFIX_PATH=$E ROS_DOMAIN_ID=1
ros2 run tf2_ros static_transform_publisher --frame-id lidar_link --child-frame-id imu_link &
rviz2 -d docs/robot-real-pi/robot_sensors.rviz
```

(`micromamba activate` no dejó `AMENT_PREFIX_PATH`: hay que exportarlo a mano. La TF
`lidar_link → imu_link` es ficticia, solo para dibujar la aceleración.)

- **Imagen por Wi‑Fi:** cruda (~0,9 MB por cuadro) no llega nunca a la Mac. Hace falta JPEG:
  `/usb_cam/image_raw/compressed` (~70–90 KB/s a calidad 50). En RViz Jazzy el transporte
  se elige con el **nombre del tópico** (`…/compressed`); `Transport Hint` no funcionó y RViz
  seguía pidiendo la imagen cruda. Nada en la Mac debe suscribirse a la cruda.
- Por internet (no en la misma red) DDS no cruza routers: Zenoh o VPN.

## Cambios en el workspace del equipo (`~/wro_controller_ws/src/peripherals`)

| Archivo | Cambio | Copia aquí |
|---|---|---|
| `peripherals/camera_publisher.py` | Publica también `/usb_cam/image_raw/compressed` (JPEG, parámetro `jpeg_quality` = 50), **solo si hay suscriptores**. Original en `camera_publisher.py.bak-antes-compressed` | [diff](robot-real-pi/peripherals/camera_publisher_compressed.patch), [script que lo aplica](robot-real-pi/peripherals/patch_camera_publisher_compressed.py) |
| `peripherals/led_light.py` (nuevo) | Tira en blanco con `brightness` (0,2 por defecto) y `led_count` (30); reenvía el color cada 1 s; la apaga al cerrar | [led_light.py](robot-real-pi/peripherals/led_light.py) |
| `launch/sensors.launch.py` (nuevo) | Ver abajo | [sensors.launch.py](robot-real-pi/peripherals/sensors.launch.py) |
| `peripherals/camera_publisher.py` | Cámara **por id de USB** (`/dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0`, vuelve a `/dev/video0` con aviso si no existe). Original en `camera_publisher.py.bak-antes-by-id` | [diff](robot-real-pi/peripherals/camera_publisher_by_id.patch), [script que lo aplica](robot-real-pi/peripherals/patch_camera_publisher_by_id.py) |
| `setup.py` | Entrada `led_light = peripherals.led_light:main`. Original en `setup.py.bak-antes-leds` | [diff](robot-real-pi/peripherals/setup_led_light.patch) |

Hay que compilar `peripherals` después de cada cambio (`colcon build --packages-select peripherals`;
la instalación es una copia). Conviene subir estos cambios al repo del equipo.

### `sensors.launch.py`

```bash
~/scripts/stop_ros.sh                       # primero, detener el stack del equipo
export ROS_DOMAIN_ID=1
source ~/wro_controller_ws/install/setup.bash
source ~/Projects/WRO-Strategies/install/setup.bash
ros2 launch peripherals sensors.launch.py [servo:=true] [leds:=true] [detector:=false]
```

Lanza la placa (`rrc_driver`: IMU), el LiDAR (5 s después: si arranca junto con la placa da
*timeout*), la cámara (7 s) y, con `detector:=true` (por defecto), `scan_adapter` →
`/robotek/scan` y `obstacle_detector` (8 s). `leds:=false` y `servo:=false` por defecto.
No lanza `acker_node` ni el motor.

**Para detenerlo:** `kill -INT` al proceso `ros2 launch` dejó los nodos hijos vivos; al
relanzar hubo dos copias de cada nodo y el LiDAR daba *timeout* (dos lectores en el puerto).
Matar también los hijos (`led_light`, `ldlidar_stl_ros2_node`, `rrc_driver`,
`camera_publisher`, `scan_adapter`, `obstacle_detector`, `servo_steer`).

## Detector de pilares en el coche real (`obstacle_detector`)

Nuevo nodo en nuestra repo: `robotek_obstacle/obstacle_detector_node.py`. Corre **la misma
percepción de la simulación** (`color_blocks` + `scan_clusters` + `associate`) sin manejar:

- `/obstacle/markers`: cilindro rojo/verde + distancia por pilar asociado (cámara + LiDAR),
  una línea por mancha de color vista por la cámara, punto gris por grupo del LiDAR del
  tamaño de un pilar.
- `/obstacle/debug_image/compressed`: cámara con recuadros (gruesos = asociados), conteo y
  decisión de giro. Solo se codifica si alguien mira.
- `/obstacle/steer` (`Float32`, rad, + izquierda): ver "Prueba de servo".

### Colores (HSV) en el coche real

Los rangos de la simulación no sirven con el piso de madera. Medidas en dos cuadros
([con luz](robot-real-pi/frames/luz.png), [en sombra](robot-real-pi/frames/sombra.png)):

| Zona | H | S | V |
|---|---|---|---|
| Pilar rojo, con luz | 0 ± 2 | ≥ 229 | 158–177 |
| Pilar rojo, en sombra | 0 | 255 | 34–61 |
| Zócalo (con luz / sombra) | 0–5 | alta | 16–70 / 1–46 |
| Piso de madera | 4–28 | 76–181 | 55–117 |
| Pilar verde | 60–78 | ≥ 221 | 66–108 |
| Reflejo del verde en el piso | 35–53 | 89–200 | 45–64 |

| Color | Simulación | Coche real (parámetros del detector) | Resultado |
|---|---|---|---|
| Rojo | H 0–8 ∪ 170–179, S ≥ 90, V ≥ 45 | H 0–4 ∪ 172–179, S ≥ 170, V ≥ 110 (`red_*`) | Con luz: de 9 recuadros falsos (piso, zócalo) a 1, el pilar ([máscara](robot-real-pi/frames/rojo_mascara_nueva.png)) |
| Verde | H 35–85, S ≥ 70, V ≥ 45 | H 56–90, S ≥ 150, V ≥ 50 (`green_*`) | Sin las manchitas del reflejo ([antes](robot-real-pi/frames/verde_reflejo_sim.png)) |
| Área mínima | 30 px | 150 px (`min_area`) | Quita motas; un pilar a 2,5 m mide ~11×22 px |

Los parámetros se leen en cada cuadro: `ros2 param set /obstacle_detector red_v_min 90`.

**Límite: rojo en sombra.** El pilar en sombra (V 34–61) no se separa del zócalo (V 1–46) por
color: con V ≥ 50 se detecta en sombra pero con luz el zócalo se une al pilar. Opciones: más
luz (tira LED con alimentación propia), exposición manual de la cámara (`manual:=true` en
`camera_publisher`), o confiar en la asociación con el LiDAR (un recuadro solo es pilar si
coincide con un grupo del tamaño de un pilar).

`color_blocks(bgr, ranges=SIM_COLOR_RANGES, min_area=30)`: los valores por defecto son los de
la simulación; verificado idéntico a la versión anterior en 202 imágenes (2 reales + 200
sintéticas). `obstacle_strategy` sigue con los rangos de la simulación: para el coche real
habrá que pasarle estos.

### Cámara frente a LiDAR: asociación y alineación de la cámara

Un recuadro de color **solo se convierte en pilar** (cilindro en RViz) si su ángulo coincide,
con menos de **0,12 rad (~7°)** de diferencia (`associate`, `angular_gate`), con un grupo del
LiDAR del tamaño de un pilar (1,5–12 cm, a menos de 2,5 m, sincronizado ±0,15 s). Así las
manchas falsas del piso o del zócalo ya se descartan si el LiDAR no ve nada ahí.

El ángulo de cada mancha se calcula con la cámara de la simulación (centrada, HFOV 60°,
inclinación 0,4 rad). Si la cámara real no mira exactamente al frente, el error no produce
pilares falsos sino **pilares perdidos**:

| Error de la cámara | Efecto en el ángulo calculado |
|---|---|
| Girada X° | Desplaza **todos** los ángulos X° |
| HFOV real ≠ 60° | Crece hacia los bordes (con 70° reales, ~5° de error en el borde) |
| Inclinación ≠ 0,4 rad | Pequeño, sobre todo en las esquinas |

Con ~5° de giro más un HFOV algo distinto, los pilares de los costados ya no se asocian; rara
vez, con dos grupos del LiDAR cerca, podría asociarse el equivocado. En RViz se ve: la línea
de color de la cámara debería pasar por el punto gris del LiDAR. **Se corrige calibrando la
cámara** (giro y HFOV con un pilar en varias posiciones conocidas), no abriendo el margen.

### Prueba de servo (`servo:=true`)

El detector decide con el signo más cercano y `servo_steer` (nuevo, `robotek_hardware`) mueve
**solo el servo** (mismo mapeo y límite ±25° que `base_adapter`; nunca el motor):

- **Rojo → derecha (−25°)**: el rojo se pasa por su derecha. **Verde → izquierda (+25°)**.
  Nada → centro; también al dejar de recibir ángulos (0,5 s) y al cerrar.
- Más cercano = pilar asociado con menor distancia LiDAR; si no hay asociación (cámara sin
  calibrar), el recuadro más alto en la imagen. **Esta segunda vía no usa el LiDAR**: una
  mancha falsa puede mover el servo. Es solo para esta prueba.
- Ángulo: `ros2 param set /obstacle_detector steer_deg 15.0`.

Verificado: con el verde a la vista `/obstacle/steer` = 0,436 rad (+25°); pruebas del paquete
6/6 (`robotek_obstacle`) y 5/5 (`robotek_hardware`) en el Pi.

## Prueba de servo y motor (`actuator_test`)

Mide el tiempo de respuesta del servo y del motor y el ángulo real de giro con la IMU y el
LiDAR. Nodo `robotek_hardware/actuator_test.py`, análisis sin ROS en `actuator_analysis.py`
(probado con datos sintéticos de retardo, constante de tiempo, velocidad y ángulo conocidos).

```bash
~/scripts/stop_ros.sh
source ~/wro_controller_ws/install/setup.bash && source ~/Projects/WRO-Strategies/install/setup.bash
A=actuator_test.launch.py
ros2 launch robotek_bringup $A test:=servo wait_button:=false                  # coche quieto
ros2 launch robotek_bringup $A test:=motor motor_pcts:="[30.0]" wait_button:=false
ros2 launch robotek_bringup $A test:=steer steer_pct:=30.0 wait_button:=false
ros2 run robotek_hardware power_monitor --ros-args -p duration:=60.0          # en paralelo
ros2 run robotek_hardware actuator_report ~/robotek-runs/<carpeta>            # re-analizar
```

Con `wait_button:=false` empieza sola en cuanto el LiDAR y la IMU dan datos (el botón no
funciona, ver abajo) y termina sola. Datos en `~/robotek-runs/<UTC>-actuator-<test>/`
(`commands.csv`, `imu.csv`, `scan.csv`, `plan.json`, `summary.json`). Arranca
`rrc_driver`, el LiDAR, `scan_adapter` y el motor: `motor:=robotek` (por defecto, nuestro
`motor_driver`) o `motor:=team` (no controla STBY, ver más abajo).

**Por SSH:** `stop_ros.sh` mata todo proceso con `ros2 launch` en su línea de comandos,
incluida la propia sesión SSH si el mismo comando lanza después la prueba: usar dos llamadas
`ssh` separadas (detener; lanzar con `setsid nohup`).

| Prueba | Qué hace | Qué mide |
|---|---|---|
| `servo` | Coche quieto: 0 → +A → 0 → −A → 0 (A = 10° y 25°), 1 s cada uno | Retardo aproximado por la vibración del chasis en la IMU (no ve el ángulo de las ruedas) |
| `motor` | Pulso recto de 0,25 s al 15, 20 y 30 % | Retardo hasta la primera aceleración (IMU) y hasta que el LiDAR ve movimiento; velocidad máxima por IMU (aceleración integrada) y por LiDAR; tiempo hasta parar; distancia total; % mínimo que mueve el coche |
| `steer` | Ruedas a ±A y 1 s de espera; después pulso de 0,25 s al 30 %; rueda por inercia | **Ángulo efectivo** de las ruedas: por el rumbo girado sobre la distancia recorrida (promedia la vibración) y por giro instantáneo / velocidad; si el signo coincide con el pedido |

**Motor: nunca más de 0,25 s seguidos** (pedido del usuario, 7 oct 2026): límite fijo en el
nodo (corta un ciclo antes, cada 20 ms) y no admite un pulso nuevo hasta un paso con motor
en 0. Además corta el motor si el LiDAR ve algo a menos de 35 cm en ±25° delante, si faltan
datos del LiDAR o de la IMU 0,5 s, al terminar y al cerrar; comprueba 1 m libre delante antes
de cada pulso; reenvía la orden cada 20 ms (el nodo de motor del equipo no tiene watchdog).
Dirección limitada a ±25°.

**Límites del método:** con el LiDAR a 10 Hz la velocidad de un pulso tan corto sale
suavizada (en la prueba sintética, 0,37 frente a 0,52 m/s reales): por eso se reporta también
la de la IMU. El ángulo efectivo usa la velocidad del LiDAR y puede salir algo mayor que el
real. La prueba de servo con el coche quieto solo da un retardo aproximado. Primer diseño de
`steer` (servo a mitad del pulso, 8 oct 2026): el coche se paraba (~0,4 s rodando) antes de
que las ruedas terminaran de girar y el giroscopio solo mostraba vibración (ángulos −2,5 /
−2,0 / +1,6° para +10 / −10 / +25°, [datos](robot-real-pi/actuator-runs/20261008T024253Z-actuator-steer/)):
por eso ahora las ruedas se giran antes del pulso.

**Botón:** el `rrc_driver` lanzado así **no publica** `/rrc/button`
(el tópico no existe), así que la prueba nunca se entera de la pulsación. Por ahora se usa
`wait_button:=false` (empieza ~9 s después de lanzar). La IMU, que en un arranque anterior no
publicaba, funcionó a 49,5 Hz.

### Resultado `test:=servo` (7–8 oct 2026, coche quieto)

[Datos](robot-real-pi/actuator-runs/20261008T021921Z-actuator-servo/). Ruido del giroscopio en
reposo σ = 0,0013 rad/s; el movimiento del servo se ve claro (picos 0,03–0,68 rad/s).

| Escalón | Empieza a moverse (orden → IMU) | Fin de la vibración |
|---|---|---|
| 10° (×4) | 56–79 ms (mediana ~64 ms) | 140–210 ms (una vez 590 ms) |
| 25° (×4) | 52–69 ms (mediana ~58 ms) | 380–540 ms |

- **Retardo orden → movimiento ≈ 60 ms** (incluye ROS, la placa y el muestreo de la IMU a 20 ms).
  Muy repetible. En simulación se usa el servo rápido estimado (`actuator_model:=true`).
- El fin de la vibración es una **cota superior** del tiempo de recorrido (el chasis sigue
  oscilando): ~0,15–0,2 s para 10° y ~0,4–0,5 s para 25°. El ángulo real y el tiempo de
  recorrido salen mejor de `test:=steer`.
- −25° pide 1069 µs, cerca del tope de 1000 µs del mapeo del equipo.

### Resultado `test:=motor` (8 oct 2026, pulsos de 0,24 s, motor del equipo)

[Datos](robot-real-pi/actuator-runs/20261008T022206Z-actuator-motor/). Coche recto, pared a
~1,07 m. Un primer intento se detuvo antes de mover el motor: solo 0,79 m libres.

| Motor | Empieza a acelerar (IMU) | Vel. máx. IMU / LiDAR | Distancia total | Hasta parar tras el corte |
|---|---|---|---|---|
| 15 % | 77 ms | 0,18 / 0,10 m/s | 2,6 cm | 0,26 s |
| 20 % | 70 ms | 0,18 / 0,11 m/s | 3,7 cm | 0,28 s |
| 30 % | 64 ms | 0,32 / 0,20 m/s | 6,0 cm | 0,42 s |

- **Retardo orden → aceleración ≈ 65–80 ms.** El coche se mueve ya desde el 15 % (con
  0,25 s de pulso); a 0,25 s todavía está acelerando, así que no hay velocidad estable ni
  relación %→m/s todavía.
- **La IMU de la placa está girada 90°** (construcción anterior, placa plana; desde el 21 oct 2026 la
  Raspberry y la RRC Lite van de canto y los ejes hay que medirlos otra vez con `imu_axes`,
  ver [roadmap](roadmap-robot-nuevo.md)): el eje hacia delante del coche es **+y** de la IMU
  (integrando `ay` sale 0,18–0,32 m/s y vuelve a ~0 al parar, coherente con el LiDAR; `ax`
  da ~0). En reposo `ax` +0,62, `ay` −0,50, `az` 9,62 m/s² (placa algo inclinada). El
  giroscopio z (rumbo) no cambia. El primer análisis usaba `ax` y además cortaba la ventana
  en la fila del corte de 0,25 s: corregidos (`FORWARD_AXIS = 'ay'`).
- La velocidad del LiDAR (10 Hz) sale ~40 % por debajo de la de la IMU en pulsos tan cortos;
  `delay_movimiento_lidar` es el tiempo hasta 2 cm de avance (0,32–0,40 s), no el inicio.

### Intentos `test:=steer` (8 oct 2026, pulsos de 0,25 s al 50 %)

1. **Detenido por seguridad** al primer pulso ("sin datos de LiDAR"): la prueba empezó ~4 s
   después de arrancar el LD19 y aún no había scans. Destapó un fallo: la comprobación de
   espacio libre aceptaba "sin scan" como distancia infinita. **Corregido:** el plan espera a
   tener LiDAR e IMU frescos (hasta 30 s) y la comprobación exige un scan reciente.
2. [Completo](robot-real-pi/actuator-runs/20261008T022604Z-actuator-steer/) (sensores listos en
   1,5 s, 1,12 m libres), pero **el coche no se movió** en ninguno de los 4 pulsos: distancia
   del LiDAR constante (±5 mm) y sin aceleración en la IMU, con el nodo de motor del equipo
   funcionando. En la prueba de motor de minutos antes sí avanzaba desde el 15 %. Causa: el
   pin STBY y un cable flojo (sección siguiente). Lo único medido: retardo orden del servo →
   giroscopio **52–88 ms**, coherente con la prueba de servo.
3. Al 30 %, tras reconectar el cable: el coche avanzó (0,12–0,21 m/s) pero con el primer diseño
   de la prueba el ángulo no se pudo medir (ver "Límites del método"). Rediseñada; **sin correr
   todavía con el diseño nuevo**: [`test:=all`](robot-real-pi/actuator-runs/20261008T024739Z-actuator-all/)
   coincidió con el motor sin STBY y no se movió.

### Motor que funcionaba a ratos y alimentación (8 oct 2026)

Síntoma: el motor movía el coche en unas pruebas y en otras no (el servo siempre respondía).
Además un cable estaba flojo (el usuario lo reconectó). Dos causas de software encontradas:

1. **STBY del TB6612 = GPIO13.** El driver de Open del equipo
   (`Testv1/open/tb6612fng_driver.py`) lo pone en alto; el **nodo ROS `motor` del equipo
   nunca lo toca**, así que solo mueve el motor si otro programa dejó GPIO13 en alto. Por eso
   funcionaba a ratos. `actuator_test.launch.py` usa ahora por defecto **nuestro
   `motor_driver`** (`motor:=robotek`), que lo pone en alto.
2. **Nuestro `motor_driver` no movía el motor al 100 %:** escribía el pin PWM en alto
   (`gpio_write`), pero con un `tx_pwm` activo en ese pin `lgpio` ignora la escritura y el
   motor quedaba al último ciclo (0 % tras parar). Al 50 % sí giraba. **Corregido:** siempre
   `tx_pwm` con ciclo 0–100 %.

Verificado con el coche en el aire: pulsos de 0,25 s al 50, 100 y 100 % → **los tres giran**
(vibración de la IMU σ 1,7 / 3,2 / 3,3 frente a 0,03 en reposo,
[datos](robot-real-pi/actuator-runs/20261008T025449Z-actuator-motor/)).

**Alimentación** (la batería alimenta el motor y el Pi): `power_monitor` (nuevo,
`robotek_hardware`) registra la batería que publica la placa (solo ~0,5 Hz) y la entrada de
5 V del Pi (`vcgencmd pmic_read_adc EXT5V_V`, ~75 Hz) con `get_throttled`.

| Situación | 5 V del Pi | Batería | Bajo voltaje |
|---|---|---|---|
| Reposo | 5,00–5,03 V | — | no |
| Servo ±10/±25° ([datos](robot-real-pi/actuator-runs/20261008T024553Z-power/)) | mín. 4,835 V (al arrancar nodos, no con el servo) | 7,84–7,86 V | no |
| Pulsos motor 50/100/100 % ([datos](robot-real-pi/actuator-runs/20261008T025440Z-power/)) | caída ≤ 83 mV (mín. 4,914 V) | 7,57–7,69 V | no |

**No pierde potencia:** el Pi se mantiene muy por encima de su umbral (~4,63 V). Los
reinicios de hoy coinciden con la tira LED al 100 % y con el cable flojo. La batería sí baja con
el uso (8,14 V → 7,6 V en ~45 min): cargarla antes de medir velocidades.

**Al 100 % desde parado el coche se encabrita** (observado por el usuario, 8 oct 2026, coche
en el suelo): las ruedas delanteras quedan en el aire un rato y **la dirección no actúa hasta
que vuelven a tocar el piso**. En la IMU: cabeceo hasta 1,8 rad/s y aceleración vertical de
−0,4 a 19 m/s² (al 50 %: 1,0 rad/s y 7,7–13,7 m/s², avanza 9,2 cm sin levantarse). Con el
morro arriba el LiDAR mira hacia arriba y la distancia de delante no sirve. Implica: no
arrancar a fondo; limitar el % de salida o subirlo en rampa (en `motor_driver` o en la
estrategia), y medir a partir de qué % se levanta.

### `test:=motor` incremental en el suelo (8 oct 2026, `motor_driver`, sin pasar del 70 %)

[Datos](robot-real-pi/actuator-runs/20261008T025907Z-actuator-motor/),
[alimentación](robot-real-pi/actuator-runs/20261008T025858Z-power/). Pulsos de 0,24 s desde
parado, de 10 % en 10 %; batería 7,57–7,61 V. Protección nueva: si un pulso levanta el morro
(cabeceo > 1,3 rad/s o aceleración vertical < 5 m/s²) no se sube más el motor.

| Motor | Empieza a acelerar | Vel. máx. IMU / LiDAR | Avance | Cabeceo máx. | az mín. (m/s²) | 5 V del Pi |
|---|---|---|---|---|---|---|
| 10 % | 72 ms | 0,12 / 0,10 m/s | 0,6 cm | 0,43 rad/s | 7,9 | −70 mV |
| 20 % | 31 ms | 0,18 / 0,20 m/s | 3,7 cm | 0,63 rad/s | 8,0 | −48 mV |
| 30 % | 32 ms | 0,34 / 0,24 m/s | 7,1 cm | 0,74 rad/s | 8,1 | −57 mV |
| 40 % | 51 ms | 0,44 / 0,27 m/s | 8,1 cm | 1,07 rad/s | 8,2 | −43 mV |
| 50 % | 52 ms | 0,53 / 0,33 m/s | 8,7 cm | 1,07 rad/s | **4,4** | −71 mV |
| 60, 70 % | omitidos: al 50 % la aceleración vertical bajó a 4,4 m/s² (el morro empieza a levantarse) | | | | | |

- Se mueve desde el **10 %**. Retardo orden → aceleración **30–70 ms** con nuestro driver.
- La velocidad máxima tras 0,24 s crece casi lineal con el %: ~0,11 m/s por cada 10 %
  (IMU); el coche todavía acelera, así que no es la velocidad de crucero.
- **Desde parado, a partir del ~50 % el morro empieza a levantarse** (al 100 % se levanta del
  todo). Arrancar por debajo del 40–50 % o con rampa.
- Alimentación: el Pi no baja de 4,915 V en ningún pulso; sin bajo voltaje.

### `test:=steer` con el diseño nuevo (8 oct 2026, ruedas giradas antes del pulso)

Pulsos de 0,24 s desde parado con las ruedas ya giradas (1 s de asentamiento). Datos:
[30 %](robot-real-pi/actuator-runs/20261008T030029Z-actuator-steer/),
[40 %](robot-real-pi/actuator-runs/20261008T030121Z-actuator-steer/),
[alimentación](robot-real-pi/actuator-runs/20261008T030021Z-power/).

| Orden | Motor | Avance | Ángulo por rumbo | Ángulo instantáneo |
|---|---|---|---|---|
| +10° | 30 % / 40 % | 5,0 / 5,1 cm | −1,8° / −0,8° | +0,3° / +3,7° |
| −10° | 30 % / 40 % | 4,6 / 5,4 cm | −5,7° / +1,5° | −0,1° / +3,7° |
| +25° | 30 % / 40 % | 1,0 / 4,8 cm | — / **+14,9°** | — / **+27,3°** |
| −25° | 30 % / 40 % | 3,9 / 4,4 cm | **−19,6°** / **−13,6°** | **−23,0°** / **−23,2°** |

- **±25°: el sentido es correcto y el ángulo efectivo está entre ~14° y ~27°**. Los dos métodos
  se separan: "por rumbo" usa como recorrido el cambio de la distancia de delante (en una curva
  infla el recorrido → ángulo menor) e "instantáneo" usa la velocidad del LiDAR, que en pulsos
  cortos sale baja (→ ángulo mayor). El valor real estará en medio (~20°).
- **±10°: no se puede medir así.** Con ~5 cm de avance el giro esperado es ~2° y queda en el
  ruido (signos al azar).
- Con las ruedas giradas el coche avanza menos (≈5 cm al 40 % frente a 8 cm recto).
- **Conclusión:** con pulsos de 0,25 s el coche recorre muy poco para medir el ángulo con
  precisión. Opciones: pulsos más largos a % bajo (requiere relajar el límite de 0,25 s), o
  medir el ángulo de las ruedas directamente (transportador o foto desde arriba) para cada µs.

### Pulsos de 1 s al 20 % con vuelta atrás (8 oct 2026)

El usuario autorizó pulsos más largos a potencia baja: `max_motor_time` hasta **1 s solo con
todos los % ≤ 30** (por defecto sigue 0,25 s). Cada pulso hacia delante va seguido, tras
parar, de uno **marcha atrás** con el mismo ángulo, % y duración (`return_back`), para volver
al punto de partida sin necesitar espacio. El LiDAR está al frente y **no ve detrás** (ningún
rayo válido entre ±150° y 180°): la comprobación trasera no actúa; el usuario deja espacio.
[Datos](robot-real-pi/actuator-runs/20261008T031013Z-actuator-all/),
[alimentación](robot-real-pi/actuator-runs/20261008T031004Z-power/).

**Velocidad de crucero al 20 %: 0,20 m/s** (LiDAR, recto, último 40 % del pulso; 15 cm en
un intento anterior a 0,15 m/s con la batería algo más alta, así que varía con el estado).

| Orden | Giro estable | Ángulo con vel. de la recta | Por rumbo | Instantáneo | Ida y vuelta |
|---|---|---|---|---|---|
| +10° | 0,107 rad/s | **+3,9°** | +5,3° | +5,5° | +3,7 cm, −2,4° |
| −10° | −0,126 rad/s | **−4,7°** | −7,2° | −7,3° | +3,5 cm, +1,3° |
| +25° | 0,531 rad/s | **+18,9°** | (no vale) | +31,3° (no vale) | +2,1 cm, −5,6° |
| −25° | −0,436 rad/s | **−15,7°** | (no vale) | −22,3° | +1,6 cm, +1,9° |

- **Las ruedas giran menos de lo pedido:** 10° → **~4–7°**; 25° → **~16–22°** (un
  intento anterior a 1 s dio +10° → 5,7°). Parece un juego o zona muerta de ~4–6° en la
  dirección; el sentido siempre es el correcto. "Con vel. de la recta" supone la misma
  velocidad en la curva (en la curva es algo menor) y tiende a quedarse corto; "por rumbo" e
  "instantáneo" usan la distancia de delante, que en curvas de 25° deja de servir.
- **Marcha atrás funciona** (nuestro `motor_driver`); cada ida y vuelta deja el coche a 1–4 cm
  (retrocede algo más) y ±2–6° del inicio.
- Alimentación: 5 V del Pi ≥ 4,827 V, sin bajo voltaje; **batería 7,33–7,39 V: cargar**.
- Para la estrategia: el modelo de dirección del coche real no es el ideal; habrá que usar
  una tabla orden → ángulo real (o compensar ~5°) y revalidar en simulación.

### Velocidad de crucero por % (8 oct 2026, pulsos de 1 s con vuelta atrás)

[Datos](robot-real-pi/actuator-runs/20261008T031324Z-actuator-motor/),
[alimentación](robot-real-pi/actuator-runs/20261008T031315Z-power/). Recto, `motor_driver`,
**batería 7,30–7,34 V (baja)**; velocidad estable del LiDAR en el último 40 % del pulso.

| Motor | Velocidad estable | Avance en 1 s | Empieza a acelerar |
|---|---|---|---|
| 10 % | 0,046 m/s | 3,6 cm | 139 ms |
| 15 % | 0,112 m/s | 9,8 cm | 84 ms |
| 20 % | 0,194 m/s | 15,1 cm | 48 ms |
| 25 % | 0,255 m/s | 21,5 cm | 53 ms |
| 30 % | 0,317 m/s | 25,4 cm | 79 ms |

- **v = 0,0137 · (% − 6,5) m/s** (recta 10–30 %, error máx. 0,9 cm/s): arranca hacia el 6,5 %
  y cada m/s cuesta ~73 %. **`robot.yaml` actualizado:** `motor_pct_per_mps` 40 → 73 y
  `motor_min_pct` 12 → 6,5 (los anteriores eran supuestos; con ellos `base_adapter` mandaba
  menos % del necesario: a 0,5 m/s pedidos, ~0,35 m/s reales).
- Medido solo hasta 30 % (0,32 m/s) y con la batería baja: con la batería cargada el coche irá
  algo más rápido para el mismo %. La simulación usa ~1 m/s o más: falta medir ese rango
  (pulsos de más del 30 %, que hoy no están autorizados más de 0,25 s).
- Alimentación: 5 V del Pi ≥ 4,80 V, sin bajo voltaje.

### Rampa a 40–60 % y freno suave (8 oct 2026)

**Rampa** (propuesta del usuario, `test:=ramp`): 0,5 s al 30 % y después 0,7 s al objetivo
(máx. 1,2 s seguidos y 60 %; por encima del 30 % solo tras el escalón), parar y volver igual
marcha atrás. [1.ª](robot-real-pi/actuator-runs/20261008T031830Z-actuator-ramp/),
[2.ª](robot-real-pi/actuator-runs/20261008T031958Z-actuator-ramp/),
[3.ª con freno suave](robot-real-pi/actuator-runs/20261008T032134Z-actuator-ramp/).

| Objetivo | Vel. estable | Cabeceo / az mín. al acelerar | Nota |
|---|---|---|---|
| 40 % | 0,41 / 0,33 m/s | 0,46 rad/s / 8,0 m/s² | no se levanta |
| 50 % | 0,39 / 0,42 / 0,44 m/s | 0,58 rad/s / 7,2 m/s² | no se levanta |
| 60 % | — | 0,85 rad/s / 5,9 m/s² | no se levanta; LiDAR inválido (el coche se desvió) |

- **Con la rampa no se levanta el morro ni al 60 %** (desde parado empezaba hacia el 50 %).
- La velocidad estable apenas sube del 40 al 50 % (0,33–0,44 m/s, menos que la recta 10–30 %
  extrapolada: 0,46 / 0,60): con 0,7 s y el LiDAR a 10 Hz hay solo 2–3 muestras estables y
  la batería estaba baja (7,3 V). A 50–60 % el coche se desvía y el rayo de delante deja de
  medir la pared (saltos de 6 m/s): medida poco fiable. Repetir con batería cargada y más
  espacio.
- La primera vez la protección saltó al 50 % por error: la caída de az (3,5 m/s²) fue en el
  **frenazo**, no al acelerar. Ahora solo se vigila mientras el motor empuja hacia delante.

**Freno suave:** el usuario vio que el freno (motor invertido 0,12 s al mismo %) **hacía
derrapar** y desaceleraba muy brusco. `motor_driver` ahora para con **rampa**: baja el % a 0
en 0,3 s en el mismo sentido y deja la rueda libre (`brake_mode:=ramp`, `stop_ramp_s`; el
anterior queda como `brake_mode:=reverse`). Igual al cambiar de sentido y en el watchdog.
Efecto medido: tiempo hasta parar 0,21–0,27 s → **0,70–0,76 s**; cabeceo en la parada
0,58–0,85 → **0,21–0,24 rad/s**. Ojo: la rampa de parada mantiene algo de motor 0,3 s después
de la orden 0 (el límite de pulso cuenta hasta la orden), y una orden nueva en el mismo
sentido espera a que termine la rampa.

### `/cmd_vel` con límites de aceleración y deceleración (8 oct 2026)

El motor ya se maneja desde `/cmd_vel` con **`base_adapter`** (como en `robot.launch.py`):
m/s → % con la calibración medida (73 %/m/s, mínimo 6,5 %) y ángulo → µs del servo. Nuevo:
la velocidad que va al motor sigue a la pedida con **`accel_limit` 1,0 m/s²** y
**`decel_limit` 0,6 m/s²** (`robot.yaml`; 0 = sin límite; al invertir el sentido pasa por 0),
para que ninguna estrategia arranque a fondo (morro arriba) ni frene en seco (derrape). Si
dejan de llegar órdenes, frena con la misma deceleración. El usuario pidió una deceleración
más larga: la rampa de parada de `motor_driver` pasa de 0,3 a **0,6 s**.

`test:=cmdvel` (`actuator_test` publica `/cmd_vel`; máx. 0,3 m/s, 1 s, con vuelta atrás):
[datos](robot-real-pi/actuator-runs/20261008T032548Z-actuator-cmdvel/), batería ~7,3 V.

| Pedido | Velocidad estable real | Tiempo hasta parar |
|---|---|---|
| 0,15 m/s | 0,18 m/s | 0,56 s |
| 0,30 m/s | 0,27 m/s | 0,74 s |

- La calibración acierta con un error de ~+20 % / −10 % (la recta no es exacta en los extremos
  y la batería estaba baja). Las rampas funcionan: arranque y parada sin levantar ni
  cabecear (cabeceo ≤ 0,33 rad/s).
- Si sigue derrapando, bajar `decel_limit` (p. ej. 0,4 m/s²) o alargar `stop_ramp_s`.

### Velocidades más altas por `/cmd_vel` (8 oct 2026)

El usuario autorizó llegar al 100 % siempre con las rampas de `base_adapter`. `test:=cmdvel`
por velocidad: subir con `cmd_accel` 1 m/s², mantener `cmd_hold` 0,6 s (ahí se mide),
frenar con 0,6 m/s² y volver igual marcha atrás. Antes de cada velocidad comprueba el espacio
(v²/2a + v·hold + v²/2d + 0,5 m: 0,95 / 1,34 / 1,83 / 2,43 / 3,53 m para 0,4 / 0,6 / 0,8 /
1,0 / 1,3 m/s) y se detiene si no cabe. Nuevo **`/robotek/estop`** (`Bool`): `motor_driver`
corta el motor al instante (sin rampa) y `base_adapter` pone la velocidad a 0; la prueba lo
usa si algo queda a menos de 0,35 m + 0,5 s·v delante.
[Datos](robot-real-pi/actuator-runs/20261008T033348Z-actuator-cmdvel/),
[alimentación](robot-real-pi/actuator-runs/20261008T033340Z-power/).

| Pedido | ≈ Motor | Real estable | Hasta parar | Avance | Cabeceo |
|---|---|---|---|---|---|
| 0,4 m/s | 36 % | 0,30 m/s | 0,95 s | 0,37 m | 0,20 rad/s |
| 0,6 m/s | 50 % | 0,42 m/s | 1,25 s | 0,63 m | 0,18 rad/s |
| 0,8 m/s | 65 % | — | — | — | no cabía (1,70 de 1,83 m) |

- Arranque y frenada suaves (sin levantar el morro, cabeceo ≤ 0,2 rad/s).
- **Por encima del 30 % el coche va ~25–30 % más lento de lo pedido:** la recta de
  calibración (10–30 %) no vale más arriba, y la **batería estaba en 6,99–7,03 V** (casi
  descargada para una 2S). Ampliar la calibración con la batería cargada.
- Faltan 0,8 / 1,0 / 1,3 m/s: necesitan ~1,9 / 2,5 / 3,6 m libres delante y detrás.

### Ángulo real de las ruedas con círculos (8 oct 2026, `test:=circle`)

Ruedas fijas a un ángulo, 4 pulsos de 1 s al 20 % con pausas (el coche recorre un arco) y la
misma secuencia marcha atrás. Se graban los scans completos (`scans.jsonl`); el análisis saca
el largo del arco con la odometría LiDAR del proyecto (`robotek_common.lidar_odometry`) y el
giro con el giroscopio: radio = arco / giro y ángulo = atan(0,13 m / radio del eje trasero).
No depende de la velocidad. Verificado con un arco sintético en una habitación (20° → < 1,5°
de error). `circle_sides:=left|right` para hacer un solo lado (pedido del usuario).
[Datos](robot-real-pi/actuator-runs/) (`*-actuator-circle`).

| Orden | Medidas (arco, giro) | Ángulo real |
|---|---|---|
| +25° | 18,1° (0,30 m, 42°) · 19,9° (0,86 m, 135°) · 18,8° (0,45 m, 67°) · 20,3° (0,79 m, 126°) | **~19,7°** |
| −25° | −17,8° (0,13 m) · −17,8° (0,26 m) · −17,4° (1,19 m, 162°) | **~−17,6°** |
| +10° | 8,7° (0,73 m, 49°) | **8,7°** |
| −10° | −8,6° (0,71 m, 47°) | **−8,6°** |

- Todos los scans se alinearon (20/20 … 80/80). Varias corridas pararon por obstáculos a < 35 cm
  o por falta de espacio delante (la protección funcionó); el ángulo vale con el arco hecho.
- **No hay zona muerta** (la estimación con pulsos de 0,25–1 s era errónea): las ruedas giran
  algo menos de lo pedido, más a fondo. **Giro máximo real ~18–20°**, no 25°, y **asimétrico**:
  a la izquierda cierra ~2° más. Las estrategias suponen 25°: en el coche real las curvas serán
  más abiertas.
- **Compensación (decisión del usuario):** mismo rango a ambos lados. `base_adapter` recibe el
  ángulo de rueda que pide la estrategia, lo limita a **17,6°** y manda al servo el ángulo que lo
  produce en ese lado (tabla inversa `wheel_table_*` en `robot.yaml`: 17,6° a la izquierda →
  ~22,1° de servo, a la derecha → 25°). Las estrategias (Open y Obstacle: `steer_limit` ahora es
  parámetro, 25° por defecto) reciben 17,6° en el coche (`robot.launch.py`) y con
  `real_car:=true`; el planificador de Obstacle escala sus arcos con el límite (idénticos a 25°).
  Sigue dentro de la regla de ±25°.

Con el motor arreglado faltan: la velocidad de crucero por encima del 30 % y con la batería
cargada,
confirmar el ángulo de las ruedas midiéndolo directamente (para separar juego de dirección y
error del método) y el freno de la marcha atrás.

## Incidentes

- **Tira LED al 100 % apagó el Pi** (30 WS2812 en blanco ≈ 1,8 A desde los 5 V del Pi). Se
  desconectó la tira. Ahora `led_light` arranca al 20 % (≈ 0,4 A) y `sensors.launch.py` la deja
  apagada por defecto. Alimentarla desde un regulador aparte.
- **El Pi se reinició/desconectó varias veces más con la tira apagada** (también al copiar
  archivos). Batería 7,99 V (2S) en reposo. Sin diagnóstico: revisar batería, regulador del Pi
  y conexión; tras reiniciar, `vcgencmd get_throttled` vuelve a `0x0` y no sirve para saber
  qué pasó. Al reiniciar arranca solo el stack del equipo (`ros_autostart`).
- **El Pi desapareció de la red durante varios minutos** tras reconectarlo: un barrido de
  `192.168.0.10/24` (ping, puerto 22) y mDNS solo encontraban el router y la Mac. Volvió solo
  con la misma IP (último reinicio 19:31). Al reconectar, esperar a que termine de arrancar;
  si no aparece, `hostname -I` en el Pi o la lista de clientes del router (`192.168.0.10`).
- Un `rsync` con `/` de más copió el contenido de `robotek_obstacle` en
  `~/Projects/WRO-Strategies/src/` del Pi; se movió a `~/Projects/sobrantes-rsync-20261007/`
  (copias, se puede borrar).

## Pendiente

- [ ] Calibrar la cámara real: giro respecto del frente, `CAMERA_HFOV` y `CAMERA_PITCH`
      (`vehicle.py`). Comparar el ángulo de la cámara con el del LiDAR con un pilar en el centro y
      a los costados. Sin esto los pilares de los costados no se asocian.
- [ ] Prueba de servo: idea de un parámetro `require_lidar` para girar solo con pilares
      confirmados por el LiDAR (no implementado).
- [ ] Probar el detector en el campo real con su iluminación; ajustar `red_v_min`.
- [ ] Alimentación: causa de los reinicios; tira LED con regulador propio.
- [ ] Subir los cambios de `peripherals` al repo del equipo.
- [ ] Lista de [robot-real.md](robot-real.md#pendiente-de-verificar-en-el-robot-por-ssh) (actualizada).
