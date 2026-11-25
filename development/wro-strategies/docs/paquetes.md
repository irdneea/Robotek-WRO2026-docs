# Organización de paquetes ROS 2

7 de octubre de 2026. Antes: `robotek_sim` (mundos + URDF) y `robotek_control` (Open,
Obstacle, auditoría, juez y runners en un solo paquete). Ahora siete paquetes de un
propósito cada uno, siguiendo la convención de la comunidad (`<robot>_description`,
`<robot>_gazebo`, `<robot>_bringup`, un paquete por función).

```
src/
├─ robotek_description/   URDF/xacro, configs de RViz                       (ament_cmake)
├─ robotek_gazebo/        mundos, tapete, puente ros_gz, launch de Gazebo   (ament_cmake)
├─ robotek_common/        librería: lidar_odometry.py, vehicle.py           (ament_python)
├─ robotek_open/          estrategia Open + perfiles                        (ament_python)
├─ robotek_obstacle/      estrategia Obstacle + perfiles                    (ament_python)
├─ robotek_evaluation/    solo simulación: auditores, servo estimado, juez,
│                          reportes, runners y arneses (tools/)              (ament_python)
├─ robotek_hardware/      solo robot real: base_adapter, motor_driver, scan_adapter,
│                          start_button, servo_steer, actuator_test,
│                          config/robot.yaml                             (ament_python)
├─ robotek_bringup/       open_challenge / obstacle_challenge / robot  (ament_python)
│
│  solo coche (vienen del workspace del equipo, desde el 9 oct 2026):
├─ rrc_lite_driver/       driver de la placa RRC Lite (fork de Hiwonder)    (ament_python)
├─ rrc_lite_msgs/         sus mensajes y servicios                          (ament_cmake)
├─ peripherals/           cámara (camera_publisher), sensors.launch, tira LED (ament_python)
└─ ldlidar_stl_ros2/      driver del LiDAR LD19 (C++, solo Linux)           (ament_cmake)
```

**El coche compila y corre solo con este repo** (`git pull` + `colcon build` en el Pi,
[flujo](robot-real-pi.md#flujo-push-en-el-mac-pull-en-el-pi)). En el Mac, `tools/macos_env.sh`
salta `ldlidar_stl_ros2` (usa cabeceras de Linux) y le pasa a CMake el Python de RoboStack para
`rrc_lite_msgs`. Detalles del driver: [src/rrc_lite_driver/README.md](../src/rrc_lite_driver/README.md).

```
robotek_open ─────┐
                  ├─► robotek_common
robotek_obstacle ─┘
robotek_evaluation ─► robotek_open, robotek_obstacle, robotek_gazebo ─► robotek_description
robotek_bringup ─► todos
```

## Reglas

- **Las estrategias solo dependen de `robotek_common`.** No pueden importar
  `robotek_evaluation` (pose real, juez, contactos): la simulación honesta queda
  garantizada por las dependencias, no solo por disciplina.
- **Open y Obstacle no se importan entre sí**; lo compartido va a `robotek_common`.
- **`vehicle.py`** guarda las medidas del coche y de los sensores para ambas estrategias;
  deben coincidir con el URDF de `robotek_description`.
- **El robot real** necesita `robotek_description`, `robotek_common`, una estrategia y
  `robotek_hardware`; no Gazebo ni evaluación. Launch: `robotek_bringup/robot.launch.py`
  ([robot real](robot-real.md)).

## Comandos

```bash
colcon build                   # los 7 paquetes, en orden de dependencias
source install/setup.zsh
ros2 launch robotek_bringup open_challenge.launch.py        # o obstacle_challenge.launch.py
bash src/robotek_evaluation/tools/run_gui_experiment.sh ...  # runners: ver README de robotek_evaluation
(cd src/robotek_open && python3 -m pytest test -q -m 'not linter')   # pruebas por paquete
```

Perfiles históricos (Open y Obstacle): borrados el 9 oct 2026; el código actual los rechaza y
cada ronda guardada tiene su propia copia en `source/profile.yaml`.
Las pruebas de estilo de la plantilla (`flake8`, `pep257`, `copyright`) se quitaron: el código
no las cumplía (>1.000 avisos); quedan las pruebas funcionales de cada paquete.

Parámetros (7 oct): cada `*_config.py` separa los **parámetros** (ROS, ajustables desde un
perfil: Open 21 = 15 de control + 6 de operación, entre ellos `steer_limit`; Obstacle 16, incluidos el estacionamiento, la geometría de la cámara y `steer_limit`) de los **valores fijos**
(`ClassVar`: Open 22, Obstacle 33), que nunca se ajustaron en ningún perfil. Mismos
números que antes (equivalencia idéntica en los tres arneses). Para cambiar un valor
fijo en una prueba: `config_with(nombre=valor)`; para volverlo ajustable, pasarlo a la
sección de parámetros.

Nombres que no cambiaron: ejecutables (`open_strategy`, `obstacle_strategy`,
`audit_pose_recorder`, …), archivos de launch, parámetros y perfiles. Las rondas
guardadas conservan las rutas de su época en `manifest.json` y `source/`.

## Verificación de la migración

- Las pruebas funcionales pasan (38 Open, 6 Obstacle, 33 evaluación).
- Equivalencia: Obstacle contra `05a0eb3` (trazas `ref-sync`, idéntico); Open contra
  `cf5add4` (17.820 pasos, 189 scans, 15 ciclos, 38 resúmenes: idéntico) y contra
  `feb2f46` (24.680 muestras de 44 rondas: idéntico).
- Rondas reales con los paquetes nuevos: ver [next-steps.md](next-steps.md).

## Hashes tras reescribir el historial

Al quitar del historial un `contacts.jsonl` de 118 MB (límite de GitHub) los commits
anteriores cambiaron de hash. Equivalencias usadas en la documentación:
`779dc63` → `feb2f46`, `0ad5978` → `cf5add4`, `f59439b` → `a2a02e0`, `bf3e989` → `ec53fb0`.
Los JSON de resultados y las rondas guardadas antes de esa fecha conservan los hashes viejos.

**Segunda reescritura (9 oct 2026):** se quitó del historial la telemetría y los datos crudos de
las rondas (`docs/*-challenge-runs/*/`, salvo los resúmenes; ver `.gitignore`): el repo pasó de
210 MB a 41 MB. Los hashes citados en la documentación ya están actualizados:
`6f37d47` → `feb2f46`, `38fc2f0` → `cf5add4`, `4f300e2` → `a2a02e0`, `bb97bdd` → `ec53fb0`,
`be3800d` → `05a0eb3`, `d1ba9a5` → `bf155c2`, `39051eb` → `1f950d1`. Copia del historial anterior:
`~/Projects/repo-backups/WRO-Strategies-before-filter-20261009.bundle` (en el Mac del usuario).

## Fuentes

- [Is there / could there be a standard robot package structure? (Open Robotics Discourse)](https://discourse.openrobotics.org/t/is-there-could-there-be-a-standard-robot-package-structure/52368)
- [Naming and Organizing Packages in Large ROS 2 Projects (Automatic Addison)](https://automaticaddison.com/naming-and-organizing-packages-in-large-ros-2-projects/)
- [Using a Python Library from another package (ROS 2 tutorial)](https://ros2-tutorial.readthedocs.io/en/latest/using_python_library.html)
