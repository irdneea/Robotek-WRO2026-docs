# Renombrado del driver de la RRC Lite (9 oct 2026)

| Antes | Ahora |
|---|---|
| paquete `ros_robot_controller` | `rrc_lite_driver` |
| mensajes `ros_robot_controller_msgs` | `rrc_lite_msgs` |
| módulo `ros_robot_controller_sdk` (`board.py`) | `rrc_lite_driver_sdk` |
| ejecutable `controller_node`, archivo `controller_node.py`, nodo `ros_robot_controller` | ejecutable y nodo `rrc_driver`, archivo `rrc_driver.py` |
| tópicos y servicios `/ros_robot_controller/…` (privados, `~/battery`) | `/rrc/…` (en el código: `rrc/battery`) |
| launch `ros2 launch ros_robot_controller wro.launch.py` | `ros2 launch rrc_lite_driver wro.launch.py` |

**Por qué:** convenciones de ROS 2 ([REP 144](https://reps.openrobotics.org/rep-0144/),
[nombres de tópicos](https://design.ros2.org/articles/topic_and_service_names.html)). `ros` en el
nombre de un paquete no aporta nada, y «controller» se confunde con un algoritmo de control. Este
paquete es el **driver** de la placa RRC Lite, un fork del de Hiwonder. No lleva el prefijo
`robotek_` porque no es diseño del equipo.

## Qué se cambió

En el **coche**, con [`rename_rrc_driver.sh`](rename_rrc_driver.sh) (ejecutado el 9 oct 2026, sin
borrar nada):

- `~/wro_controller_ws/src`: carpetas, archivos y nombres dentro del driver, de los mensajes y de
  `peripherals` (launch, `joystick_control.py`). `colcon build` correcto (4 paquetes).
- `~/scripts/ros_autostart.sh` (modo obstacle: `ros2 launch rrc_lite_driver wro.launch.py`) y
  `~/scripts/stop_ros.sh`, que reconoce **los dos** nombres de proceso.
- Las carpetas viejas `build/` e `install/` del driver y los mensajes se movieron a la copia.
- **Copia de todo** en `~/rename-backup-20261009T212959/`.
- Dos reglas de la primera versión del script eran demasiado amplias: `package_name=` y
  `get_package_share_directory('…')` quedaron como `rrc_driver`. Se corrigieron a mano en el
  coche y en el script.

En **este repo**: `robotek_hardware` (todos los nodos y su `package.xml`), `robot.launch.py`,
`actuator_test.launch.py`, `tools/usb_stress_test.py`, las configuraciones de RViz, la copia de
`sensors.launch.py` y los scripts de autoarranque, la documentación vigente, la guía
[`learn/01`](../../../learn/01-battery-guard/README.md) y el código del equipo en el submódulo
`Robotek-WRO2026` (`src/open|obstacle/robot_node.py`).

**Probado en el coche:**

- `ros2 run rrc_lite_driver rrc_driver` → nodo `/rrc_driver` y 15 tópicos `/rrc/…`.
- `/rrc/imu_raw` a 49,3 Hz; `/rrc/battery` publica.
- `rrc_lite_msgs` con 20 interfaces.
- Los 7 nodos de `robotek_hardware` cargan los mensajes nuevos.

## Copia en el repo

Desde el 9 oct 2026 el driver y los mensajes renombrados están en este repo
([`src/rrc_lite_driver`](../../../src/rrc_lite_driver/README.md), `src/rrc_lite_msgs`), junto con
`peripherals` y `ldlidar_stl_ros2`. El coche los compila desde el repo
([flujo push/pull](../../robot-real-pi.md#flujo-push-en-el-mac-pull-en-el-pi)); `~/wro_controller_ws`
queda como copia antigua.

## Qué NO se cambió (siguen con los nombres viejos)

- `~/Documents/Testv1`: archivo de experimentos y auditorías del equipo.
- El **modo Open del equipo** (`~/Documents/Testv1/open/run_open.sh`), que usa su propia copia
  `~/Documents/wro_controller_ws-copy`. Esa copia tiene los nombres viejos y funciona por su cuenta.
  No hay que ejecutar los dos stacks a la vez.
- Rondas, registros y diffs anteriores al 9 oct en `docs/` (historia).
- [ros-robot-controller-oficial.md](../../ros-robot-controller-oficial.md): describe el código
  **oficial** de Hiwonder, que se sigue llamando así.

## Deshacerlo

```bash
ssh user@192.168.0.10
WS=~/wro_controller_ws; B=~/rename-backup-20261009T212959
mv $WS/src $WS/src-renamed && cp -a $B/src $WS/src
cp -a $B/extra$HOME/scripts/. ~/scripts/
mv $WS/install/rrc_lite_driver $WS/install/rrc_lite_msgs $WS/build/rrc_lite_driver $WS/build/rrc_lite_msgs $B/
mv $B/install/* $WS/install/ && mv $B/build/* $WS/build/
cd $WS && source /opt/ros/jazzy/setup.bash && colcon build
```

Y en este repo, `git revert` del commit del renombrado.
