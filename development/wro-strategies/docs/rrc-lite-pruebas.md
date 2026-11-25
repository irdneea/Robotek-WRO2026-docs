# Pruebas de la placa RRC Lite en el coche

> **Nombres nuevos (9 oct 2026):** el driver de la placa es `rrc_lite_driver` (antes
> `ros_robot_controller`), con mensajes `rrc_lite_msgs`, nodo `rrc_driver` y tópicos `/rrc/…`. Este
> documento ya usa los nombres nuevos, también al contar pruebas anteriores, que se hicieron con
> los viejos: [nombres nuevos](robot-real-pi/rename/README.md).

Plan para probar **todas las funciones de la placa** (la misma de Hiwonder MentorPi; qué hace
cada una en [ros-robot-controller-oficial.md](ros-robot-controller-oficial.md)). Herramienta:
`rrc_test` (`robotek_hardware`). **Corrida en el coche el 9 oct 2026**: ver
[Resultados en el coche](#resultados-en-el-coche-9-oct-2026). Documentación oficial de Hiwonder
(esquemático, protocolo, lecciones del firmware) descargada en
[rrc-lite/oficial/](rrc-lite/oficial/README.md).

## La placa (ficha de Hiwonder)

[hiwonder.com/products/rrc-lite](https://www.hiwonder.com/products/rrc-lite), leída el 9 oct 2026:

| Parte | Especificación |
|---|---|
| Chip | STM32F407VET6, Cortex‑M4 a 168 MHz; descarga por serie. **Nuestra placa: v1.0** (serigrafía de detrás) |
| IMU | **MPU6050** a bordo (6 ejes: giroscopio y acelerómetro de 3 ejes cada uno), con un interruptor para la IMU en la placa |
| Motores | **4 puertos de motor con encoder y control de velocidad PID**, driver SA8870C con protección de sobrecorriente |
| Servos | **4 PWM** (5–8,4 V en los parámetros, 5–12 V en la tabla comparativa; puente para elegir 5 V o la tensión de entrada) y **2 de bus serie** (6–12 V) |
| Botones | **2 personalizables** (*custom key*, los `id` 1 y 2 de `button`) y **1 de reset** del STM32 |
| Avisos | 1 zumbador, **3 LED** según los parámetros (la tabla comparativa de la misma página dice 2 LED de usuario), **2 RGB**; no se lista pantalla OLED |
| Alimentación | entrada de **6 a 14 V**; salida de 5 V / 5 A con protocolo PD para la Raspberry Pi 5 |
| Comunicación | 1 USB serie Type‑C (plug and play) y 1 puerto I²C de 4 pines; **sin CAN** (la versión grande de la placa sí lo trae) |
| Protecciones | polaridad inversa, sobrecorriente, sobrecalentamiento, contracorriente |
| Tamaño | 85 × 56 × 17 mm, 32 g |

Capturas de la página completa (Playwright, 9 oct 2026, 2×) en [docs/rrc-lite/](rrc-lite/):
[página completa](rrc-lite/hiwonder-rrc-lite-pagina-completa.jpg),
[descripción 1](rrc-lite/hiwonder-rrc-lite-descripcion-1.jpg) (incluye la tabla que compara las tres
versiones de la placa), [descripción 2](rrc-lite/hiwonder-rrc-lite-descripcion-2.jpg) y
[parámetros, interfaces y medidas](rrc-lite/hiwonder-rrc-lite-especificaciones-e-interfaces.jpg).

### Lo nuevo que muestran las capturas

- **IMU:** es una **MPU6050**.
- **Botones:** hay **2 personalizables** (los `id` 1 y 2 de `button`) y **1 de reset**. Antes solo se
  usaba el 1.
- **LED:** los parámetros dicen **3 LED**, pero la tabla comparativa de la misma página dice **2 de
  usuario**. Aclarado en el coche: **2 de usuario** (ids 1 y 2, azules) más un piloto de
  alimentación fijo.
- **Servos PWM:** la página dice **5–8,4 V** en un sitio y **5–12 V** en otro.
- **Versión Lite:** no tiene CAN y solo trae un puerto I²C y un USB Type‑C.

### Lo que añade la documentación oficial (descargada el 9 oct 2026)

Carpeta de Google Drive enlazada desde la página de la RRC Lite («code and schematics»). Es la
documentación de la **ROS Robot Controller** (la placa grande, mismo firmware y protocolo): sirve
para el protocolo y el firmware, pero los conectores de la Lite pueden estar en otro sitio.
Índice y qué leer en [rrc-lite/oficial/README.md](rrc-lite/oficial/README.md).

- **Protocolo** (lección 14): confirma el del SDK (`0xAA 0x55`, función, longitud, datos, CRC8 de
  función + longitud + datos; little-endian; 1 000 000 baud). Servo PWM: pulso **500–2500 µs**
  (0–180°), con tiempo de movimiento en ms y desviación (offset) de −100 a +100 por servo. Botón:
  la placa envía `PRESSED 0x01`, `LONGPRESS 0x02`, `CLICK 0x20`, `DOUBLE_CLICK 0x40`: el firmware
  sí reporta pulsación larga y doble click; los descarta el `get_button()` del SDK (ver
  [ros-robot-controller-oficial.md](ros-robot-controller-oficial.md)). La IMU va en 6 `float`
  (acel. en g, giro en °/s).
- **Alarma de batería baja del firmware**: el umbral se compila en `global_conf.h` (6300 mV para
  baterías de 8 V, 9600 mV para 12 V) y avisa con el zumbador, que en este coche no suena.
  `battery_guard` avisa antes (6,8 V, RGB en rojo). La batería se mide con el ADC (PB0) cada 50 ms; a la
  Raspberry le llega a ~1 Hz.
- **Zumbador**: SEA‑12085 a 5 V, encendido por un transistor S8050 desde PA8 (la explicación del
  esquemático dice PA4; el esquemático y la lección 3 dicen PA8). Que no suene puede ser el
  zumbador o el transistor Q3.
- **Servos PWM**: en el esquemático v1.1 los 4 conectores son J1 (PA11), J2 (PA12), **J4 (PC8)** y
  J5 (PC9), todos a **5 V**; la explicación del esquemático (igual en v1.0 y v1.2) dice dos a 5 V y dos a la tensión de entrada (VIN).
  En el coche el servo está en **J4**, que responde como **canal 2** del protocolo. La Lite tiene un
  puente para elegir 5 V o VIN: comprobar en la placa a qué tensión está J4 antes de cambiar de
  servo.
- **Nuestra placa es la v1.0** (serigrafía de detrás, confirmada el 9 oct 2026). Por eso:
  - **IMU MPU6050** (la v1.2 cambia a QMI8658), por I²C (PB10/PB11, interrupción PB12). Vale la
    lección `L05-imu-mpu6050.pdf`.
  - **Medida de batería**: según las preguntas frecuentes de la introducción al hardware, en la v1.0
    **dos patas del STM32F407 van puenteadas** a propósito (VDD y la referencia interna de tensión);
    sin ese puente la lectura de batería sale mal. No tocarlo. La lectura del coche (7,26 V) es
    plausible; contrastarla una vez con un multímetro en los bornes de la batería, porque
    `battery_guard` depende de ella.
  - El esquemático descargado es el de la **v1.1** (no hay uno de v1.0 en la carpeta): lo que
    difiere de la v1.0 conocida es ese puente.
- **Botones**: K1 en PE0 y K2 en PE1 (pull‑up de 10 kΩ, activos a nivel bajo); BOOT0/BOOT1 a masa
  por 10 kΩ (arranque desde la flash); RST = NRST.
- **LED**: el LED de usuario va en PE10 (activo a nivel bajo); hay pilotos de 5 V y 3,3 V fijos.
- **Firmware**: FreeRTOS; partes `Peripherals`, `Chassis` (diferencial, mecanum, **Ackermann**),
  `Porting`, `System`. Hay que fijar el tipo de chasis en `app.c`: si no, «los motores pueden
  descontrolarse»; no aplica mientras no se usen los motores de la placa.
- **Salida 5 V / 5 A** para la Raspberry: regulador RT8289; **interruptor de habilitación de
  motores** (SW, «enable switch»): apagado, los motores de la placa no se mueven.

Consecuencias para el coche: la placa **sí tiene entradas de encoder**, pero el coche no tiene
encoder (solo giroscopio y LiDAR); sin encoder conectado, `set_motor` en rps no tiene lazo
cerrado. Y el mínimo de 6 V de la placa es lo que importa para `battery_guard` (avisa a 6,8 V:
0,8 V de margen antes de que la placa se apague).

## Comprobar que es esta placa (hecho el 9 oct 2026)

Resultado en el Pi del coche ([detalle y nombres estables](robot-real-pi.md#los-usb-y-sus-nombres-estables-9-oct-2026)):

- La placa es el USB **`1a86:55d4`** «USB Single Serial» (serie `586B015678`, driver `cdc_acm`), **el
  mismo id que la regla udev del repo oficial**. Nuestras notas anteriores decían «CH340»: no era
  correcto.
- Aparece como `/dev/ttyACM0` y como `/dev/serial/by-id/usb-1a86_USB_Single_Serial_586B015678-if00`.
  **No existe `/dev/rrc`**: la regla del equipo (`99-ttyACM0.rules`) no está instalada.
- El `rrc_driver` del equipo abre el nombre `by-id`, no `/dev/ttyACM0`. El `Board()` oficial
  usa `/dev/rrc` por defecto; el fork cambió eso.

Para repetirlo:

```bash
ssh user@192.168.0.10 'lsusb | grep -i 1a86; ls -l /dev/serial/by-id /dev/rrc 2>&1; grep -rn "by-id\|ttyACM\|/dev/rrc" ~/wro_controller_ws/src/rrc_lite_driver/rrc_lite_driver/*.py'
```

## Preparar

Solo hace falta el nodo de la placa; el stack del equipo (con el motor) se para antes.

```bash
~/scripts/stop_ros.sh
```

```bash
source ~/wro_controller_ws/install/setup.bash && source ~/Projects/WRO-Strategies/install/setup.bash
export ROS_DOMAIN_ID=1
ros2 run rrc_lite_driver rrc_driver
```

En otra terminal del Pi, con el mismo `source`:

```bash
ros2 run robotek_hardware rrc_test
```

Con el coche en el suelo y quieto corre solo las pruebas seguras (nada se mueve). Los
resultados quedan en `~/robotek-runs/<fecha>-rrc-test/` (`results.json` con los datos y
`summary.txt`).

## Pruebas

| Prueba | Qué hace | Cómo se juzga |
|---|---|---|
| `topics` | comprueba que la placa publica `imu_raw` y `battery` y recibe `set_buzzer`, `set_led`, `set_rgb`, `set_oled`, `set_motor`, `pwm_servo/set_state` y `enable_reception`; lista aparte `acker_servo/set_state` y `bus_servo/set_state` | PASS / FAIL |
| `enable` | manda `enable_reception = True`; en el nodo oficial sin esto no se publica nada | INFO |
| `battery` | 8 s de lecturas | PASS si hay datos entre 5,5 y 9 V; da frecuencia y mínimo/media/máximo |
| `imu` | 4 s con el coche **quieto** | PASS si ≥ 40 Hz, norma de la aceleración = g ± 1 m/s² y giroscopio con media < 0,03 rad/s; WARN si falla lo último; informa si la orientación sale vacía (lo esperado) |
| `button` | 20 s para pulsar: un click, un doble click, una pulsación larga | PASS si llega algún evento; lista los pares `(id, state)`. Oficial: solo sale `state` 1 |
| `buzzer` | tres tonos: 440, 880, 1760 Hz | MANUAL (oír) |
| `led` | los 3 LED de la placa (`led_ids`, por defecto 1, 2 y 3), 3 parpadeos cada uno | MANUAL (ver) |
| `rgb` | los 2 RGB de la placa (confirmados en la ficha) en rojo, verde, azul y apagado, **nivel 40/255** (la tira LED al 100 % reinició el Pi el 8 oct) | MANUAL (ver) |
| `oled` | dos líneas de texto | MANUAL (la ficha no lista pantalla: sin módulo OLED conectado no se verá nada) |
| `joy`, `sbus` | escucha 3 s por si hay mando o receptor de radio | INFO (sin periférico no llega nada: normal) |

## Pruebas que mueven algo (opt‑in)

Nunca están en la lista por defecto. Con el coche **levantado y las ruedas libres**:
`wheels_in_air:=true`.

| Prueba | Qué hace | Precaución |
|---|---|---|
| `acker_servo` | servo de dirección del equipo (`acker_servo/set_state`): 0 → +10° → 0 → −10° → 0 | solo existe en el fork; se omite si falta. 10° está muy por debajo del límite de 25° |
| `pwm_servo` | servos PWM de `pwm_ids` (por defecto ninguno) ±`pwm_delta` µs (100) y de vuelta a 1500 | nombrar el id del servo a mover; no mover uno cuyo mecanismo no se conoce |
| `board_motor` | cada puerto de motor de la placa (`motor_ids`) a `motor_rps` (0,3, máximo 0,5) durante `motor_time` (0,5 s, máximo 1 s) | el motor del coche es el TB6612 del Pi, no estos puertos; sin encoder el PID de la placa no tiene realimentación; reenvía a 50 Hz y pone 0 al terminar, ante un error y con Ctrl+C |
| `pwm_read`, `bus_read` | lee posición/offset de servos PWM o de bus | el SDK oficial espera la respuesta sin límite: si la placa no contesta, el nodo queda bloqueado y hay que reiniciarlo. No necesitan `wheels_in_air` |

```bash
ros2 run robotek_hardware rrc_test --ros-args -p tests:="[acker_servo,board_motor]" -p wheels_in_air:=true
ros2 run robotek_hardware rrc_test --ros-args -p tests:="[all]" -p wheels_in_air:=true -p pwm_ids:="[1]"
ros2 run robotek_hardware rrc_test --ros-args -p tests:="[imu,battery]" -p imu_seconds:=10.0
```

El servo de dirección y el motor del coche tienen además `actuator_test`
([robot-real-pi.md](robot-real-pi.md)), que los mide con la IMU y el LiDAR.

## Resultados en el coche (9 oct 2026)

Con el stack del equipo parado, solo `rrc_driver` del fork (`ros2 run rrc_lite_driver
rrc_driver`) y `rrc_test`. Resultados en el Pi: `~/robotek-runs/20261009T231032Z-rrc-test/`
(automáticas) y `~/robotek-runs/20261009T231151Z-rrc-test/` (manuales).

| Función | Resultado | Detalle |
|---|---|---|
| `topics` | PASS | todos los `set_*`, `imu_raw`, `battery`, `button`, `joy`, `sbus` y el `acker_servo/set_state` del fork |
| Recepción | activa sola | `imu_raw` ya salía a 49 Hz **antes** de mandar `enable_reception`: el fork llama a `board.enable_reception()` en el constructor |
| `battery` | PASS | 7,26 V, ±0,004 V; llega a **~1 Hz** (no 0,5 Hz) |
| `imu` | WARN (aceptable) | 49,3 Hz; norma de la aceleración 9,62 m/s²; sesgo del giroscopio quieto: x 0,002, **y 0,047**, z 0,0056 rad/s. El de y es fijo (σ 0,0015): sesgo, no movimiento. La estrategia usa z y lo calibra tras Start |
| Botones | **OK** | la placa tiene, de izquierda a derecha y de arriba abajo, **K2, K1** y en otra columna **BOOT, RST**. K1 → `id 1, state 1` y K2 → `id 2, state 1`, un mensaje por pulsación (3 de 3 en cada uno). BOOT y RST no se prueban (BOOT es el modo de programación del STM32; RST reinicia la placa). En la primera corrida de `rrc_test` no llegó nada: no se pulsó K1/K2 dentro de los 20 s |
| Zumbador | **no suena (averiado)** | 440, 880 y 1760 Hz por `set_buzzer`: silencio. Los alumnos ya habían avisado de que se quemó antes. Los pitidos de `start_button` y `battery_guard` no se oirán: no depender de ellos |
| LED | **2 de 3 controlables** | `set_led` con id 1 y 2: parpadean en **azul** (un solo color; el mensaje no lleva color). Id 3: no parpadea; el tercer LED ya estaba encendido fijo antes de la prueba: probablemente el de alimentación, no controlable por software |
| RGB | **OK** | `set_rgb` índice 1 = RGB de la **izquierda**, índice 2 = de la **derecha**; rojo, verde y azul visibles en los dos a nivel 40/255. Usados por `status_leds` para mostrar el estado del coche, a brillo **2/255** (a 40 y a 5 se reflejaban en la cámara; [estados](robot-real.md#luces-de-estado-rgb-de-la-placa)) |
| OLED | sin módulo | no hay pantalla conectada; `set_oled` no se prueba |
| Motores de la placa | sin conectar | ningún motor en los puertos de la placa (la tracción va al TB6612 del Pi); `board_motor` no se prueba |
| Servo de dirección | único servo conectado | el fork lo manda por `acker_servo/set_state` → `board.pwm_acker_set_position()`, que lo envía **fijo al servo PWM 2** (`pwm_servo_set_position(duration, [[2, position]])` en `rrc_lite_driver_sdk/board.py`). El servo está en el conector serigrafiado **J4**: J4 = canal PWM 2 del firmware |
| Dirección | **OK** | coche levantado. `rrc_test` `acker_servo` (±10°) se movió, pero ±10° se ve poco (primero pareció «derecha»). Repetido a mano con ±20° sostenido 6 s: **+20° (1879 µs) → izquierda**, **−20° (1155 µs) → derecha**, mirando desde atrás; 1500 µs deja las ruedas **rectas**. El signo de `servo_us()` (`mapping.py`) es correcto. Para comprobar el sentido a ojo, usar ≥ 20° |
| `joy`, `sbus` | INFO | sin mando ni receptor: no llega nada (normal) |

## Qué anotar tras la primera corrida

1. ¿`topics` da FAIL? Las diferencias con el nodo oficial son lo que hay que mirar en el fork
   ([comparar con el Pi](ros-robot-controller-oficial.md#comparar-con-el-pi-cuando-conecte)).
2. Qué `state` salen en `button` (oficial: solo 1; `start_button` acepta 1 y 5).
3. La frecuencia real de `imu_raw` (~49 Hz medida) y de `battery` (~0,5 Hz) y el sesgo del
   giroscopio con el coche quieto.
4. Lo MANUAL: si sonó, parpadearon los 3 LED, se encendieron los 2 RGB, y si hay algo en el OLED.
5. Con `enable` primero: ¿`imu_raw` ya salía antes de enviar `enable_reception`? Si sí, el
   fork activa la recepción por su cuenta.

## Cómo se verificó sin el coche

En el Mac (RoboStack, `tools/macos_env.sh`): se compilaron los mensajes oficiales
(`driver/ros_robot_controller_msgs` de Hiwonder/MentorPi, hoy `rrc_lite_msgs` en el coche) y un nodo falso imitó la placa
(IMU a 50 Hz, batería a 0,5 Hz, botón, recepción de `set_*` y el servicio `pwm_servo/get_state`).
`rrc_test` dio PASS en `topics`, `battery`, `imu` y `button`, y los `set_*` llegaron todos.
Eso valida el flujo de la herramienta, **no la placa**. Las partes de análisis tienen pruebas
unitarias (`test_rrc_analysis.py`).
