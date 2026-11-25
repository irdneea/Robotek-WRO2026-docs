# Robot real: launch y calibración

> **Nombres nuevos (9 oct 2026):** el driver de la placa es `rrc_lite_driver` (antes
> `ros_robot_controller`), con mensajes `rrc_lite_msgs`, nodo `rrc_driver` y tópicos `/rrc/…`. Este
> documento ya usa los nombres nuevos, también al contar pruebas anteriores, que se hicieron con
> los viejos: [nombres nuevos](robot-real-pi/rename/README.md).

7 de octubre de 2026. Las estrategias son las mismas que en simulación; en el coche las
rodean los drivers del equipo y los adaptadores de `robotek_hardware`.

> Lo encontrado en el Pi del coche (acceso, stack del equipo, sensores en RViz desde la Mac,
> detector de pilares con la cámara real, prueba de servo): [robot-real-pi.md](robot-real-pi.md).

## Qué cambia respecto de la simulación

| Simulación | Robot real (repo del equipo `Robotek-WRO2026/src`) | Adaptación |
|---|---|---|
| Gazebo publica `/scan` (0 rad adelante) | STL-19P: 0° **atrás** (frente 180°, izq. 240°, der. 120°) | `scan_adapter` rota π → `/robotek/scan` |
| `/imu` | `/rrc/imu_raw` (rad/s, convención ROS) | remapeo |
| `/camera/image` | `/usb_cam/image_raw` | remapeo |
| `/cmd_vel` al plugin Ackermann | servo RRC Lite en µs + motor TB6612 en % | `base_adapter` |
| Motor con marcha atrás | el nodo del equipo solo avanza | `motor_driver` con marcha atrás |
| Inicio automático | botón de la placa | `start_button` → `/start`; estrategias con `auto_start: false` |
| Reloj `/clock` | reloj de pared | `use_sim_time: false` |

Servo (mapeo del equipo): centro 1500 µs, 550/29 µs/° hacia un lado y 500/29 hacia el otro,
`SERVO_SIGN = −1`, tope mecánico 29°; las estrategias limitan a 25°.

## Correr en el robot

```bash
# en el Raspberry Pi 5 (Ubuntu 24.04, ROS 2 Jazzy), con el workspace compilado
source install/setup.bash
ros2 launch robotek_bringup robot.launch.py challenge:=open
ros2 launch robotek_bringup robot.launch.py challenge:=obstacle             # v3: tres vueltas y aparca
ros2 launch robotek_bringup robot.launch.py challenge:=obstacle mode:=laps  # v3: solo las vueltas (sin hueco)
ros2 launch robotek_bringup robot.launch.py challenge:=obstacle mode:=park  # v3: solo aparcar
ros2 launch robotek_bringup robot.launch.py challenge:=obstacle strategy:=v1 # el nodo original (tres vueltas)
# si la placa, el LiDAR y la cámara ya corren aparte (p. ej. peripherals sensors.launch.py):
ros2 launch robotek_bringup robot.launch.py challenge:=open controller:=false lidar_package:= camera:=false
```

Desde el 3 nov 2026 el Obstacle lanza el **v3** (`obstacle_strategy_v3`, `obstacle_v3.yaml`), aún sin probarlo en
el coche; antes era el nodo original (`obstacle_sensors_v1.yaml`), que sigue con `strategy:=v1`.

Desde el 1 nov 2026 `robot.launch.py` arranca solo todo el hardware, con los tiempos de
`sensors.launch.py`: la placa (`rrc_lite_driver controller.launch.py`: IMU, botón, servo), el LiDAR
(`peripherals lidar.launch.py`) 5 s después (si arranca junto con la placa da *timeout*) y la cámara
(`peripherals camera_publisher`, también publica `.../compressed` para RViz) a los 7 s. Antes buscaba
`rrc_lite_driver.launch.py`, que no existe, y no lanzaba el LiDAR: la placa y el LiDAR había que
lanzarlos aparte. **Sin probar todavía en el coche.**

Pulsar el botón (K1): la estrategia calibra el giroscopio y arranca. **Las reglas obligan a
calibrar después de Start**, no antes: §9.9 prohíbe *«make any sensor calibrations on the
vehicle»* en la preparación, y §9.11 pide que, tras encender, el coche solo espere el botón de
Start, sin otra interacción ([reglas](WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md)).
La calibración dura 0,3 s en Open y 1,0 s en Obstacle. Por lo mismo, **no usar K2** ni ningún
interruptor para elegir sentido o modo: sería meter datos (§9.9); el sentido lo detecta la
estrategia.

### Luces de estado (RGB de la placa)

Sustituyen a los pitidos, porque el zumbador está quemado. El nodo `status_leds` arranca por
defecto con `robot.launch.py` (`status_leds:=false` lo apaga). **Brillo 2/255** (parámetro
`level`): elegido en el coche el 9 oct 2026; con 40 y con 5 la luz se reflejaba en la cámara, con
2 se ve bien y no molesta. RGB izquierdo = índice 1 de `set_rgb`, derecho = índice 2.

| Estado | RGB izquierdo | RGB derecho |
|---|---|---|
| Arrancando (primeros 15 s, sensores aún sin datos) | apagado | apagado |
| **Listo, esperando Start** (LiDAR, IMU y cámara con datos en el último segundo) | verde | verde |
| Falta un sensor antes de Start | rojo | azul = LiDAR, magenta = IMU, amarillo = cámara |
| Calibrando tras Start | azul | azul |
| Corriendo la ronda (y tras parar con el botón) | apagado | apagado |
| Terminado (`DONE`, `PARKED`) | verde parpadeando | verde parpadeando |
| Fallo de la estrategia (sentido sin resolver, atascado, `FAULT`) | rojo | rojo |
| Batería baja: cambiarla (el coche sigue) | rojo parpadeando | rojo parpadeando |

Antes de responder «Yes» al juez: **verde en los dos = todo listo**. Con un sensor que falta, el
rojo de la izquierda dice «no listo» y el color de la derecha cuál falta; si faltan varios se
muestra el primero en este orden: LiDAR, IMU, cámara. Durante la ronda las luces van apagadas
aunque un sensor falle (la estrategia ya frena sola sin datos).

Qué estado de la estrategia da cada color (`/robotek/state`):

| `/robotek/state` | Estrategia | Luces |
|---|---|---|
| (nada aún), `WAIT_START`, `WAIT_SENSORS` | antes de Start (Open / Obstacle) | verde, o rojo + sensor que falta |
| `CALIBRATE` | las dos | azul |
| `DETECT_DIRECTION`, `FOLLOW`, `TURN`, `RECOVER`, `FINISH`, `OPERATOR_STOP`, `WAIT_SENSOR` y el resto | corriendo o parada con el botón | apagado |
| `DONE`, `PARKED` | terminada | verde parpadeando |
| `FAULT`, `DIRECTION_FAULT`, `STALLED`, `PARK_FAIL` | fallo | rojo fijo |

Cómo funciona: las dos estrategias publican el nombre de su estado en `/robotek/state`
(`String`, *latched*, solo al cambiar); `battery_guard` publica `/robotek/battery_low` (`Bool`,
*latched*) al parar por batería; `status_leds` mira además si llegaron datos de `/robotek/scan`,
`/rrc/imu_raw` y la cámara en el último segundo (`max_age`). Durante los
primeros 15 s (`boot_grace`) no marca sensores que faltan, mientras arrancan los drivers. Solo
manda un mensaje a la placa cuando cambia el color (y 4 veces por segundo al parpadear). Al
parar el nodo (Ctrl+C) apaga los dos RGB. Solo muestra: no cambia la conducción ni recibe
órdenes del equipo (§9.9–9.11). Lógica en `robotek_hardware/status_colors.py`, con pruebas
(`test_status_colors.py`). El magenta del IMU y el rojo de fallo se añadieron al esquema acordado.

**Probado en el coche el 9 oct 2026** (sensores reales con `sensors.launch.py`, estados
simulados publicando en `/robotek/state` y `/robotek/battery_low`): verde con los tres sensores;
rojo + amarillo al parar la cámara; azul con `CALIBRATE`; apagado con `FOLLOW`; verde
parpadeando con `DONE`; rojo parpadeando con batería baja; rojo + azul sin LiDAR; apagado al
cerrar con Ctrl+C. Falta verlo con la estrategia de verdad (Start, ronda y fin).

**Volver a pulsar el botón para el coche** (dos pitidos). Desde el 9 oct 2026, porque en la
primera ronda el coche chocó y no había forma de detenerlo. Cualquier pulsación después de la
primera (con 1,5 s de antirrebote) publica `/robotek/stop` (Bool true), y entonces:

- `base_adapter` pone el motor a 0 al instante y lo mantiene, aunque sigan llegando
  `cmd_vel`;
- `motor_driver` corta el motor sin rampa e ignora los comandos;
- la estrategia Open pasa a `OPERATOR_STOP`, del que no sale, y guarda el evento
  `operator_stop` en `events.jsonl`.

Para otra ronda, reiniciar el launch. Probado en la Mac: `base_adapter`, sin el coche, dejó el
motor en 0 % con `cmd_vel` a 1 m/s; en simulación (`20261009T123736Z-operator-stop-check-…`)
la estrategia paró en el siguiente ciclo de control. **Falta probarlo en el coche.**
Obstacle no escucha `/robotek/stop`, pero el motor se para igual por `base_adapter` y
`motor_driver`.

**Batería baja: aviso para cambiarla, sin parar el coche** (por defecto en `robot.launch.py`
con `challenge:=open` y `obstacle`). El nodo `battery_guard` lee `/rrc/battery`
(mV, ~1 Hz medido el 9 oct) y, con **5 lecturas seguidas por debajo de 6,8 V** (~5 s; una lectura
baja suelta no cuenta, ni una lectura de 0 mV de la placa), publica
`/robotek/battery_low`: los dos RGB **parpadean en rojo** ([luces](#luces-de-estado-rgb-de-la-placa)).
El aviso queda hasta reiniciar el launch con otra batería, así que se ve también después de la
ronda. **No para el coche** (petición del equipo, 9 oct 2026; antes publicaba `/robotek/stop` bajo
6,6 V). Se desactiva con `battery_guard:=false` y el límite se cambia con `battery_min_v:=7.0`.

Por qué 6,8 V: es 3,4 V por celda de la LiPo 2S, poca carga restante; conviene cambiarla antes de
la siguiente ronda. Por debajo de ~3,0 V por celda (6,0 V) la batería se daña, y 6 V es también el
mínimo de la RRC Lite ([ficha](https://www.hiwonder.com/products/rrc-lite)): quedan 0,8 V de margen.
El firmware de la placa tiene su propia alarma a 6,3 V, pero avisa con el zumbador, que no suena.
La batería 2S se midió en 7,0–8,1 V y en 7,26 V en reposo el 9 oct (6,40 V tras unas horas de
pruebas sin cargar).

**El motor de tracción va a tener su propia batería** (decisión del equipo, 9 oct 2026): la que
mide la placa alimentará solo la electrónica (Raspberry Pi, RRC Lite, servo). Así no habrá caídas
de tensión por el motor; las 5 lecturas seguidas quedan para filtrar lecturas sueltas (el servo
al girar, fallos de la placa), y la batería del motor **no la vigila nadie**: medirla aparte.
Probado: la lógica (`mapping.LowVoltage`) y, en el coche, el aviso y el parpadeo rojo.

La telemetría queda en
`~/robotek-runs/<fecha>-<desafío>/` (mismos archivos que en simulación, sin pose real).
Las partes que falten (paquete de la placa, `usb_cam`, `lgpio`) se saltan con un aviso, así
que el launch también se puede probar en un PC.

## Verificado sin robot

- `robotek_hardware/test/test_mapping.py`: mapeo del servo idéntico al del equipo, tope 25°,
  inversión del modelo de bicicleta (también en marcha atrás), motor con signo, rotación del scan.
- Prueba de punta a punta en el PC: Gazebo hace de robot, un nodo convierte su `/scan` en uno
  "como el STL-19P" (0° atrás) y `robot.launch.py` (con `use_sim_time:=true`, solo para esta
  prueba) corre `scan_adapter`, `base_adapter`, `motor_driver`, `start_button` y el Open.
  Con `/start` publicado a mano: **3 vueltas y DONE en 19,9 s**.
  (El plugin de Gazebo debe ir con `ackermann_acceleration:=30` y `steer_p_gain:=20`, como
  en las rondas validadas; con los valores por defecto el v4 no completa las curvas, con o
  sin adaptadores.)

## Primera ronda Open en el coche (8 oct 2026): falló, 0 puntos

`open_realcar_v4`, velocidad completa, botón, batería 7,37 V
([registro](open-challenge-runs/20261008T172740Z-realcar-hw-v4-r1/round.json)). Chocó de frente
con el muro a los ~2,9 s de Start, antes de la primera esquina.

- **Causa:** el sentido salió de la cámara (`cw camera_confirmed`) y era falso. La pared beige
  de la sala, por encima del muro negro, entra en el rango HSV naranja (O = 434 px, B = 0;
  [cuadro](open-challenge-runs/20261008T172740Z-realcar-hw-v4-r1/camera/1791480486.995.png),
  [máscara](open-challenge-runs/20261008T172740Z-realcar-hw-v4-r1/camera/1791480486.995-mask.png)).
  Cuando a la izquierda se abrió la esquina (L 0,62 → 2,58 m), el coche siguió recto en
  "CW" hasta el muro.
- **Sin detección de atasco:** siguió mandando v = 1,28 (100 % PWM) contra el muro hasta que
  se paró a mano.
- **Por confirmar:** durante ~1 s mandó girar a la derecha y el rumbo subió a +0,5 rad; a
  plena potencia las ruedas delanteras podrían perder agarre.
- Para la próxima: limitar la máscara de color al piso (por debajo del muro), medir los
  colores reales de las líneas, o decidir el sentido con el LiDAR; y empezar con un tope de
  motor menor.

## Pendiente de verificar en el robot (por SSH)

- [x] Nombre del launch de `rrc_lite_driver`: **no existe** `rrc_lite_driver.launch.py`;
      el nodo es `ros2 run rrc_lite_driver rrc_driver` (el equipo lo lanza dentro de
      `wro.launch.py`) (7 oct 2026). `robot.launch.py` usa `controller.launch.py` desde el 1 nov 2026.
- [x] Driver del LiDAR: `ldlidar_stl_ros2` configurado como **LD19** (`peripherals lidar.launch.py`),
      `/dev/ttyUSB0`, tópico `/scan`, frame `lidar_frame`, ángulos 0…2π antihorarios con el frente
      en π (igual que asume `acker_lidar_node`) → `angle_offset: π`, `reverse: false`.
      Pendiente comprobarlo con un objeto delante (7 oct 2026).
- [x] `motor_pct_per_mps` y `motor_min_pct` (`config/robot.yaml`): medidos 73 %/m/s y 6,5 %
      (8 oct 2026, 10–30 %, batería baja); repetir con la batería cargada y por encima del 30 %.
- [x] Marcha atrás del TB6612 con el nodo nuevo: funciona (8 oct 2026, pulsos de 1 s al 20 %
      con vuelta al punto de partida, ±4 cm). Falta medir el freno. Hacia delante ya funciona
      (8 oct 2026, tras corregir el 100 % y con STBY = GPIO13 en alto; el nodo del equipo no
      controla STBY): [robot-real-pi.md](robot-real-pi.md#motor-que-funcionaba-a-ratos-y-alimentación-8-oct-2026).
- [x] Servo: latencia ~60 ms; ángulo real medido con círculos: 10° → 8,7°/8,6°, 25° → ~19,7°
      (izq.) / ~17,6° (der.) ([detalle](robot-real-pi.md#ángulo-real-de-las-ruedas-con-círculos-8-oct-2026-testcircle));
      compensado por lado en `base_adapter` hasta 17,6° simétricos; estrategias con
      `steer_limit` 17,6° en el coche y en `real_car`.
- [ ] Cámara: inclinación y campo de visión reales (`robotek_common/vehicle.py`). Colores HSV
      reales ya medidos para el detector ([robot-real-pi.md](robot-real-pi.md#colores-hsv-en-el-coche-real)).
- [ ] Alimentación: el Pi se reinició varias veces (una con la tira LED al 100 %).
- [ ] Largo real del robot (define el largo del estacionamiento) y altura del LiDAR frente a los
      topes de 10 cm.
- [ ] CPU del Pi 5 con el planificador del Obstacle y la búsqueda del estacionamiento.
