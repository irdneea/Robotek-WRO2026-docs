# Control del motor en la RRC Lite: 2024 frente a ahora

Notas del 8 nov 2026. Comparé dos versiones del código que mueve el motor de la placa RRC Lite:

- **2024:** el repositorio [coach/ros2_hiwonder](https://github.com/coach/ros2_hiwonder), del
  19 nov 2024, con el MentorPi. Tiene el nodo de Hiwonder sin cambios
  (`src/driver/ros_robot_controller/`) y una demo (`RRCLite_demo/motor_control_node.py`, que manda 0.2 rps al
  motor 2 una vez por segundo).
- **Ahora:** `rrc_lite_driver` de robotek-learn (`src/rrc_lite_driver/`), que es lo que corre hoy en el coche.

La copia de `src/rrc_lite_driver/` de WRO-Strategies es más antigua. Tiene el `× 0.75`, el `-rps` y la reconexión,
pero no envía el tipo de motor ni el nivel de batería.

## Lo que no cambió

- **SDK:** el `board.py` actual es el `ros_robot_controller_sdk.py` de Hiwonder con parches. El paquete del
  motor sigue siendo `PACKET_FUNC_MOTOR`, subcomando `0x01`, con `id - 1` y la velocidad en rps como float.
- **Mensaje:** `MotorsState` con `id` y `rps`. Ahora es de `rrc_lite_msgs`; antes, de `ros_robot_controller_msgs`.
- **Control de velocidad:** lo hace la placa con el encoder del motor.

## Lo que cambió

| | `ros2_hiwonder` (2024) | `rrc_lite_driver` (ahora) |
| --- | --- | --- |
| Tópico | `/ros_robot_controller/set_motor` | `/rrc/set_motor` |
| Signo | `rps` tal cual | **`-rps`** (`rrc_driver.set_motor_state`); el signo final se fija con `rrc_motor_sign` en `robot.yaml` |
| Escala | `rps` tal cual | **`rps × 0.75`** dentro de `board.set_motor_speed` |
| Tipo de motor | no se envía (queda el de fábrica de la placa) | `set_motor_type` (paquete `0x05`), tipo 2 = JGB27; se reenvía cada 3 s con el coche parado y después de cada reinicio de la placa |
| Nivel de batería | no se envía | `set_battery_level` (paquete de sistema `0x01`), 6900 mV como el SDK LanderPi |
| Puerto serie | `/dev/rrc` | `/dev/rrc_lite` o `/dev/ttyACM0`, con reconexión si se resetea el USB |
| Watchdog | no | detiene los motores si dejan de llegar comandos |
| Motor usado | id 2 (la demo) | `rrc_motor_port: 4` (M4) en `robot.yaml` |

## Qué significa en la práctica

- **El mismo `rps` gira más lento que en 2024.** La placa recibe el 75 % del valor y lo interpreta con el modelo de
  encoder JGB27. El "rps" de la placa no son vueltas reales del motor 310 (ver los comentarios de `robot.yaml`).
  Los rps de 2024 no sirven para los perfiles de hoy.
- **El `motor_rps_per_mps` de `robot.yaml` ya incluye el 0.75**, porque se midió con este driver.
- **Riesgo:** el `× 0.75` está oculto en `board.py`, no en un parámetro. Si alguien reemplaza el SDK por el original
  de Hiwonder, el coche irá un 33 % más rápido (1/0.75) sin ningún aviso. Si cambia el tipo de motor o deja de
  enviarse, la escala también cambia.

Más sobre el nodo oficial de Hiwonder: [ros-robot-controller-oficial.md](ros-robot-controller-oficial.md).
