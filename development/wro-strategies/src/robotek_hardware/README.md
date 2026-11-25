# robotek_hardware

Solo para el **robot real**: adapta las estrategias (que hablan `/cmd_vel`, `/scan`,
`/imu`, `/camera/image`, `/start`, como en la simulación) al hardware del coche del
equipo (`Robotek-WRO2026/src`).

| Nodo | Qué hace |
|---|---|
| `base_adapter` | `/cmd_vel` → servo RRC Lite (µs, mapeo del equipo, tope 25°) + motor (%, con signo, calibrado), con límites de aceleración/deceleración (`accel_limit`, `decel_limit`) |
| `motor_driver` | TB6612FNG del equipo **con marcha atrás** (`/motor_vel` −100..100 %), pone STBY (GPIO13) en alto, parada suave en rampa (`stop_ramp_s`) |
| `scan_adapter` | scan del LiDAR (en el coche: driver LD19, frente en π) → `/robotek/scan` con 0 rad adelante |
| `start_button` | botón de la placa → `/start` y pitido |
| `gpio_button` | pulsador en el GPIO 16 (a GND, pull-up interno) → `/robotek/gpio_button` (Bool, `true` = pulsado) y log; solo avisa |
| `rear_range` | Sensor de distancia VL53L0X en el I2C del Pi (0x29, bus 1) → `/robotek/rear_range` (Range, metros) y `/robotek/rear_range_mm` (Int32, milímetros; `-1` si no ve nada). Arranca con el launch del coche (`rear_range:=false` lo quita); solo avisa. Arranca el sensor con la secuencia de la librería de Pololu (ajustes de ST y calibración de referencia) y mide en continuo (~24 Hz). Aun así, el sensor del coche mide de más y muy cerca casi no cambia. Lecturas crudas contra una pared (9 nov 2026, regla desde la pared a la cara del sensor salvo donde se dice): 10 mm → 70, 20 → 75, 30 → 77, 40 → 83, 50 → 96, 85 → 138 (LiDAR), 170 → 231 y ~420 → ~476 (foto). El nodo interpola en esa tabla (`table_raw_mm`, `table_mm`); pasado el último punto sigue con pendiente 1 y por debajo del primero con la del primer tramo, nunca menos de 0. Entre 1 y 4 cm el crudo solo cambia 2–6 mm por cm con ±3 mm de ruido, así que ahí acierta a ±1 cm; desde 5 cm, a ±5 mm (a 50 mm publica 48–52). `correct:=false` publica el crudo. Unas medidas con un libro (188 a 100 mm y 332 a 200 mm) no se repitieron contra la pared y no se usan. Si el sensor deja de responder 0,5 s o da 10 errores de I2C seguidos (le pasó en el coche: se reinició y volvió con sus registros de fábrica), el nodo lo vuelve a abrir y repite todo el arranque en menos de 5 s. |
| `actuator_test` | prueba de servo y motor con IMU y LiDAR (pulsos de motor ≤ 0,25 s; hasta 1 s solo a ≤ 30 %; vuelta atrás tras cada pulso); `actuator_report` re-analiza una corrida. Launch `robotek_bringup actuator_test.launch.py` |
| `power_monitor` | registra batería (placa) y 5 V del Pi (`vcgencmd`) con las banderas de bajo voltaje |
| `battery_guard` | **por defecto en `robot.launch.py`**: si la batería (`/rrc/battery`) baja de **6,6 V** (3 lecturas seguidas, ~6 s) publica `/robotek/stop` y pita 3 veces; el coche queda parado hasta reiniciar el launch. También actúa al arrancar con la batería baja. Se desactiva con `battery_guard:=false`; otro límite con `battery_min_v:=6.8` |
| `rrc_test` | prueba **todas las funciones de la placa RRC Lite** (IMU, batería, botón, zumbador, LED, RGB, OLED, joy, sbus, servos, motores de la placa); las que mueven algo van aparte y con `wheels_in_air:=true`. Plan: [docs/rrc-lite-pruebas.md](../../docs/rrc-lite-pruebas.md) |
| `servo_steer` | prueba en banco: ángulo (`Float32`, rad, + izquierda) → **solo el servo** (mismo mapeo y tope que `base_adapter`, nunca el motor); centra si deja de recibir |

Calibración en `config/robot.yaml` (los valores marcados MEASURE hay que medirlos).
Conversiones puras y probadas en `mapping.py`. Lanzar con
`ros2 launch robotek_bringup robot.launch.py challenge:=open|obstacle`.
Pruebas en el Pi (sensores en RViz, detector de pilares, `servo_steer`):
[docs/robot-real-pi.md](../../docs/robot-real-pi.md).
