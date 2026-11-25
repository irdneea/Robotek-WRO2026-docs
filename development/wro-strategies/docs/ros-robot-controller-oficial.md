# `ros_robot_controller` oficial de Hiwonder (MentorPi) y qué usar en el coche

> **Nombres en nuestro coche (desde el 9 oct 2026):** este documento describe el código **oficial** de
> Hiwonder con sus nombres (`ros_robot_controller`, `ros_robot_controller_msgs`,
> `/ros_robot_controller/…`). En el coche el fork se llama `rrc_lite_driver` (mensajes
> `rrc_lite_msgs`, nodo `rrc_driver`, tópicos `/rrc/…`): [nombres nuevos](robot-real-pi/rename/README.md).
>
> Cómo cambió el control del motor desde 2024 (signo, `× 0.75`, tipo de motor):
> [rrc-lite-motor-2024-vs-ahora.md](rrc-lite-motor-2024-vs-ahora.md).

Notas del 9 oct 2026 leídas **del repositorio público**
[Hiwonder/MentorPi](https://github.com/Hiwonder/MentorPi) (commit `fb6d9969`, 16 ene 2026),
no del Pi: el Pi no respondía (el Mac estaba en `192.168.31.x` y el coche en `192.168.8.x`).
El código del coche es un **fork del equipo** (`~/wro_controller_ws`): hay que compararlo con
este (ver [Comparar con el Pi](#comparar-con-el-pi-cuando-conecte)). Las partes que dependen
del fork están marcadas con **(fork)**.

Qué sale del repo oficial y dónde está:

| Carpeta del repo | Contenido |
|---|---|
| `driver/ros_robot_controller/` | nodo `ros_robot_controller` y su SDK serie (`ros_robot_controller_sdk.py`) |
| `driver/ros_robot_controller_msgs/` | mensajes y servicios de la placa |
| `driver/controller/` | cinemática (`ackermann.py`, `mecanum.py`), odometría (`odom_publisher_node.py`), EKF |
| `peripherals/` | LiDAR, cámara, filtro IMU, joystick, teleop por teclado |
| `example/self_driving/` | ejemplo de conducción autónoma de Hiwonder |

## La placa RRC Lite

- STM32 por USB serie, **1 000 000 baud**. El SDK abre `/dev/rrc` (regla udev
  `99-ttyACM0.rules`, vendor `1a86`, product `55d4`: ignora ModemManager y da permisos). En
  nuestro Pi aparece como `/dev/ttyACM0` (`1a86:55d4`, ver [robot-real-pi.md](robot-real-pi.md)).
- Paquete: `0xAA 0x55 | función | longitud | datos | CRC8`. Funciones: 0 SYS, 1 LED, 2 BUZZER,
  3 MOTOR, 4 PWM_SERVO, 5 BUS_SERVO, 6 KEY, 7 IMU, 8 GAMEPAD, 9 SBUS, 10 OLED, 11 RGB.
- La recepción empieza **desactivada** (`enable_recv = False`): el hilo del nodo solo publica
  cuando alguien manda `True` a `~/enable_reception`. Es lo que explica que, lanzado a mano,
  el `controller_node` del Pi no publicara `button` (ver
  [robot-real-pi.md](robot-real-pi.md)) mientras `imu_raw` y `battery` sí salían **(fork)**:
  habría que ver si el fork activa la recepción por su cuenta.

## Lo que publica el nodo (`/ros_robot_controller/…`)

| Topic | Tipo | Datos y unidades |
|---|---|---|
| `imu_raw` | `sensor_msgs/Imu` | aceleración = g × 9,80665 (m/s²); giro = °/s → rad/s; **orientación 0,0,0,0**; covarianzas fijas (gyro 0,01; accel 0,0004) |
| `battery` | `std_msgs/UInt16` | mV (7,3 V → 7300). Solo cuando la placa lo manda (~1 Hz medido con `rrc_test` el 9 oct) |
| `button` | `ButtonState` | `id` (1 o 2) y `state`. En el código oficial **solo sale `state` 1 (pulsar)**: el SDK devuelve CLICK como `(id, 0)`, que el nodo no reconoce y registra «Unhandled button event»; doble click, triple y pulsación larga se descartan. Los estados 2–7 de su tabla no llegan con este código; `start_button` acepta 1 y 5 porque el fork podría publicar 5 (por comprobar) |
| `joy` | `sensor_msgs/Joy` | mando de juego conectado a la placa (ejes y botones) |
| `sbus` | `Sbus` | canales de un receptor de radiocontrol aéreo |

## Lo que recibe

| Topic / servicio | Tipo | Para qué |
|---|---|---|
| `set_buzzer` | `BuzzerState` (`freq`, `on_time`, `off_time`, `repeat`) | pitidos: lo usa `start_button` (`battery_guard` ya no pita: avisa por RGB) |
| `set_led` | `LedState` (`id`, `on_time`, `off_time`, `repeat`) | LED de la placa (parpadeo) |
| `set_rgb` | `RGBStates` (índice 1…, r, g, b) | LED RGB de la placa |
| `set_oled` | `OLEDState` (`index` = línea, `text`) | texto en una pantalla OLED; la ficha de la placa no la lista: haría falta un módulo aparte |
| `set_motor` | `MotorsState` (lista de `{id 1–4, rps}`) | motores de la placa en **vueltas por segundo** |
| `pwm_servo/set_state` | `SetPWMServoState` (posición, offset, `duration`) | servos PWM 1–4 (1500 = centro) |
| `pwm_servo/get_state` | servicio | leer posición y offset del servo |
| `bus_servo/set_state`, `set_position` | | servos serie (no los usa este coche) |
| `enable_reception` | `Bool` | activa o apaga la lectura de la placa |
| `init_finish` | `Trigger` | indica que el nodo está listo |

Al arrancar pone los 4 motores a 0; al cerrar con Ctrl+C también. **No tiene watchdog**: si
los comandos dejan de llegar, el último valor sigue activo.

**(fork)** En el coche el servo de dirección se manda por
`/ros_robot_controller/acker_servo/set_state` con `SetAckerServoState` (`position` en µs,
`duration`): esa interfaz **no existe en el repo oficial**, es del equipo.

> La placa es la **RRC Lite** ([ficha de Hiwonder](https://www.hiwonder.com/products/rrc-lite); en el
> repo oficial «rrc»: `/dev/rrc`): STM32F407, 4 puertos de motor con encoder y PID, 4 servos PWM,
> 2 servos de bus, 3 LED, 2 RGB, zumbador, entrada de 6–14 V. Especificaciones y cómo probarla
> función por función: [rrc-lite-pruebas.md](rrc-lite-pruebas.md).

## Qué se podría usar en el coche

Ya en uso: IMU (solo giroscopio), batería, botón (Start / Stop), zumbador y servo.
**En el coche el zumbador está quemado** (9 oct, [resultados](rrc-lite-pruebas.md#resultados-en-el-coche-9-oct-2026)):
los avisos tienen que ir por los RGB o los LED 1 y 2.

1. **Avisos con zumbador y LED RGB** (`set_buzzer`, `set_rgb`, `set_led`): código de pitidos
   por estado (calibrando el giroscopio, listo, vuelta 1/2/3, parada por batería, parada por
   atasco) o colores en la placa. Sin coste de CPU; sirve en el campo, sin pantalla.
2. **OLED** (`set_oled`, solo si hay un módulo conectado): mostrar la tensión de la batería y el estado de la estrategia antes de
   pulsar Start, para no necesitar SSH.
3. **Segundo botón** (`id` 2): la ficha confirma **2 botones personalizables** más uno de reset.
   K1 publica `id 1` y K2 `id 2` (probado el 9 oct). **No usarlo para elegir sentido ni modo en
   una ronda**: las reglas (§9.9, §9.11) prohíben meter datos con botones o interruptores y
   permiten un solo botón de Start. Solo sirve fuera de las rondas (pruebas).
4. **Pulsación larga**: el SDK la descarta. Se podría parchear el fork para publicarla y
   usarla como apagado limpio. Cambia código del equipo; solo si hace falta.
5. **Batería**: `battery_guard` avisa (RGB en rojo) bajo 6,8 V, sin parar el coche
   ([robot-real.md](robot-real.md)). Con la lectura a ~1 Hz no sirve para estimar el
   hundimiento de tensión por pulso de motor.
6. **Motores de la placa**: `set_motor` con `rps` (el oficial convierte m/s → rps con
   `speed / (π · diámetro)`, diámetro 0,067 m por defecto en `ackermann.py`). El coche usa el
   TB6612 del equipo por GPIO, no los puertos de la placa. Sería una alternativa con
   **control de velocidad por la placa** si los puertos tuvieran encoder; no se sabe si este
   coche los tiene (no hay encoder según [AGENTS.md](../AGENTS.md)), así que no probarlo sin
   ruedas en el aire.
7. **Corrección de la IMU**: el repo trae `imu_calib` y `imu_complementary_filter`
   (`peripherals/launch/imu_filter.launch.py`, con `use_mag: False`, estimación de sesgo y
   ganancia adaptativa) y publica `imu_corrected`. Nuestra estrategia calibra el giroscopio
   tras Start, así que solo valdría para comparar el sesgo; cuidado: el launch oficial lee
   `/home/ubuntu/ros2_ws/src/calibration`, ruta que no existe en el Pi (usuario `user`).
8. **`joy` y `sbus`**: control manual con mando o radio para sacar el coche de la zona o
   mover sin estrategia. Requiere el receptor; no lo usa nadie hoy.
9. **Teleop** (`peripherals/joystick_control.py`, `teleop_key_control.py`): publican
   `controller/cmd_vel`. Referencia para un teleop propio hacia `/cmd_vel` que `base_adapter`
   ya acepta.

## Cosas del repo oficial que no coinciden con nuestro Pi

- `servo_config.yaml`: el nodo oficial lee los offsets de los servos de
  `/home/ubuntu/software/Servo_upper_computer/servo_config.yaml`. En el Pi (`user`) no
  existe: el nodo solo escribe un error y sigue.
- `ackermann.py` supone otro coche (`wheelbase = 0.145`, `track_width = 0.133`,
  `wheel_diameter = 0.067`, tope 45°) y manda el servo como `1500 + 2000·grados/180` µs. El
  nuestro usa `wheelbase = 0.13`, tope de **25°** (regla pedida) y la tabla del equipo
  (550/29 y 500/29 µs/°). No reutilizar sus constantes.
- El `launch` oficial arranca `ros_robot_controller` con el parámetro `imu_frame`
  (`imu_link`); en el Pi se lanza con `ros2 run … controller_node` **(fork)**.
- Variables de entorno que usan los launch oficiales: `MACHINE_TYPE`, `LIDAR_TYPE` (`LD19`
  o `MS200`) y `need_compile`. Faltan en un `ros2 run` suelto.

## Comparar con el Pi (cuando conecte)

Solo lectura; no hace falta parar el stack del equipo. Primero el SSH
([robot-real-pi.md](robot-real-pi.md)): `user@192.168.0.10`, Mac en el Wi‑Fi del coche.

```bash
ssh user@192.168.0.10 'ls ~/wro_controller_ws/src; cd ~/wro_controller_ws/src && git log --oneline -3 2>&1 | head'
```

```bash
rsync -a user@192.168.0.10:wro_controller_ws/src/ros_robot_controller/ /tmp/pi-ros_robot_controller/
```

```bash
diff -ru /tmp/mentorpi/MentorPi/driver/ros_robot_controller /tmp/pi-ros_robot_controller | head -300
```

Qué mirar en la diferencia:

1. ¿`controller_node` es el mismo archivo con otro nombre (`setup.py`, `entry_points`)?
2. ¿Dónde activa `enable_reception`? ¿Por eso publica `imu_raw` y `battery` pero no `button`?
3. `SetAckerServoState` y `acker_servo/set_state`: quién lo escucha y cómo pasa µs a la
   placa (¿`pwm_servo_set_position`?).
4. `acker_node`, `acker_lidar_node`, `motor`, `led`: qué publican, a qué frecuencia y con qué
   watchdog (el `motor` del equipo no tiene watchdog y su STBY no se sube).
5. Mensajes: `ros_robot_controller_msgs` del Pi frente a `driver/ros_robot_controller_msgs`
   (solo deberían añadirse mensajes, no cambiar los existentes).
6. `ros_autostart.service` y `wro.launch.py`: qué arrancan y si lanzan `battery_guard`
   (no: es nuestro, solo en `robot.launch.py`).

Con el Pi accesible también se puede inspeccionar en vivo, sin tocar nada:

```bash
ssh user@192.168.0.10 'source ~/wro_controller_ws/install/setup.bash && ROS_DOMAIN_ID=1 ros2 topic list -t'
```

```bash
ssh user@192.168.0.10 'source ~/wro_controller_ws/install/setup.bash && ROS_DOMAIN_ID=1 ros2 interface list | grep -i ros_robot_controller_msgs'
```

Cuidado con `pkill -f` por SSH (se mata la propia sesión) y con no borrar nada en el Pi.
