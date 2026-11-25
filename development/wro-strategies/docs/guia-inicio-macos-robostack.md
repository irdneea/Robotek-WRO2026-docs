# Empezar desde cero en la Mac: RoboStack, Gazebo y rondas

21 de octubre de 2026. Guía para dejar una Mac con Apple Silicon corriendo la simulación
del coche **con el robot nuevo** (medidas del 20–21 oct, URDF con piezas del STEP).
Todo sale de **RoboStack** (`ros2`, `gz`, `colcon`, RViz). **No se usa el ROS de
Homebrew** (`/opt/homebrew/opt/ros2-jazzy`): `tools/macos_env.sh` lo quita del entorno.
Los límites y mediciones de la Mac están en [simulacion-macos.md](simulacion-macos.md); qué
falta por probar con el robot nuevo, en [roadmap-robot-nuevo.md](roadmap-robot-nuevo.md).

## 1. Requisitos

- Mac con Apple Silicon (probado en M4 Pro, macOS Darwin 27) y las herramientas de línea de
  comandos de Xcode (`xcode-select --install`).
- `micromamba` (`brew install micromamba`). Solo se usa para crear el entorno.
- `git` y acceso a [coach/WRO-Strategies](https://github.com/coach/WRO-Strategies).

## 2. Clonar el repositorio

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/coach/WRO-Strategies.git
cd WRO-Strategies
git submodule update --init --recursive   # Robotek-WRO2026 (STL del equipo)
```

## 3. Crear el entorno RoboStack (una vez)

El entorno esperado está en `~/Projects/WRO/.mamba/jazzy` (Python 3.12, ROS 2 Jazzy,
Gazebo Harmonic `gz-sim8`). Es el que creó el equipo el 29 de septiembre:

```bash
micromamba create -y -p ~/Projects/WRO/.mamba/jazzy \
  -c robostack-jazzy -c conda-forge --strict-channel-priority \
  python=3.12 ros-jazzy-ros-base ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher ros-jazzy-rviz2 ros-jazzy-xacro \
  colcon-common-extensions gz-sim8

micromamba install -y -p ~/Projects/WRO/.mamba/jazzy \
  -c robostack-jazzy -c conda-forge \
  ros-jazzy-rviz-imu-plugin ros-jazzy-compressed-image-transport
micromamba install -y -q -p ~/Projects/WRO/.mamba/jazzy -c conda-forge scipy
```

Versiones con las que se probó: `gz-sim8` 8.10.0, `gz-rendering8` 8.2.2, `ogre-next` 2.3.3,
`ros-jazzy-ros-gz-sim` 1.0.23, `py-opencv` 4.13, `numpy` 2.5.3, `pytest` 9.1.
Para otro directorio: `source tools/macos_env.sh /ruta/al/entorno`.

> **No instales `ros2-jazzy` de Homebrew para este proyecto.** Si ya lo tienes, no estorba:
> `macos_env.sh` borra sus variables (`COLCON_PREFIX_PATH`, `GZ_SIM_RESOURCE_PATH`,
> `GZ_SIM_SYSTEM_PLUGIN_PATH`, …) y su `bin/` del `PATH`, y avisa si `ros2`, `gz` o `colcon`
> no vienen de RoboStack. Su Gazebo además necesita cuatro variables a mano y su `gz topic`
> no arranca; no se usa.

## 4. Preparar la terminal y compilar

En **cada terminal nueva**, desde la raíz del repositorio:

```bash
cd ~/Projects/WRO-Strategies
source tools/macos_env.sh
```

La primera vez y **tras cada cambio en `src/`** (la instalación es una copia):

```bash
colcon build --packages-ignore robotek_hardware     # tarda ~1–3 min la primera vez
source tools/macos_env.sh                           # recarga install/
```

`robotek_hardware` es solo del coche real. `ldlidar_stl_ros2` se salta solo en la Mac.
Avisos que se pueden ignorar: `ros2-argcomplete.zsh ... no such file` y
`not found: .../ldlidar_stl_ros2/.../local_setup.zsh`.

Comprobaciones rápidas:

```bash
command -v ros2 gz colcon          # los tres deben apuntar a ~/Projects/WRO/.mamba/jazzy/bin
grep -c homebrew install/setup.sh  # debe imprimir 0
xacro src/robotek_description/urdf/robotek.urdf.xacro real_sensors:=true | head -3
```

Si `grep` imprime algo distinto de 0, una compilación se hizo con variables de Homebrew:
`source tools/macos_env.sh` y vuelve a compilar (el script ya las limpia).

No compiles ni edites `src/robotek_evaluation/tools/` **mientras corre un lote**: los
runners se ejecutan desde `src`.

## 5. Probar el código (sin simulador)

```bash
PYTHONPATH=src/robotek_common:src/robotek_hardware:src/robotek_obstacle:src/robotek_open \
  python -m pytest -q -p no:launch_testing -p no:launch_ros \
  src/robotek_common src/robotek_hardware src/robotek_obstacle src/robotek_open
```

`-p no:launch_testing -p no:launch_ros` evita un error de `pluggy` con los plugins de ROS.
`PYTHONPATH` hace que se prueben las **fuentes** y no la copia instalada. Estado a 21 oct:
99 pasan, 4 fallan (ver [roadmap](roadmap-robot-nuevo.md#fase-2-pruebas-unitarias)).

## 6. Lanzar la simulación

### 6.1 Solo Gazebo con el robot

```bash
ros2 launch robotek_gazebo robotek_sim.launch.py field:=open real_sensors:=true
```

Abre el campo Open con **el robot nuevo por defecto** (`robotek_description/urdf/robotek.urdf.xacro`)
en (0, −1) y **la ventana de Gazebo con solo la vista 3D** (sin árbol de entidades, spawner ni
otras tarjetas). La cámara arranca a 0,7 m del coche. Argumentos útiles:

| Argumento | Por defecto | Para qué |
|---|---|---|
| `field` | `obstacle` | `open` (sin obstáculos) u `obstacle` (señales + parqueo) |
| `world` | vacío | ruta a un SDF; reemplaza a `field` |
| `gui` | `true` | `false` = servidor sin ventana |
| `gui_config` | vacío | disposición de la ventana; vacío = `config/gui_scene_only.config` (solo 3D). Gazebo normal: `$ROBOSTACK_ENV/share/gz/gz-sim8/gui/gui.config` |
| `spawn_x`, `spawn_y`, `spawn_z`, `spawn_yaw` | 0, −1, 0.05, 0 | pose inicial |
| `real_sensors` | `false` | `true` = cámara 6 fps, LiDAR ±110°, IMU del coche real (usar con el robot real) |
| `sensor_noise` | `false` | ruido gaussiano en LiDAR y giroscopio |
| `ackermann_velocity_limit`, `ackermann_steer_p_gain`, `ackermann_acceleration` | 1.0, 1.0, 2.0 | límites del plugin Ackermann |
| `robot` | vacío | otro URDF/xacro/SDF |
| `spawn` | `true` | `false` = no crea el robot |

En macOS, `gz sim` no puede llevar servidor y ventana en un solo proceso: el launch arranca
el servidor con `-s` y la ventana con `gz sim -g --gui-config …` como proceso aparte
(`gazebo_gui`). En Linux va todo junto.

Para cerrar todo:

```bash
bash src/robotek_evaluation/tools/clean_sim.sh
```

### 6.2 Estrategia Open o Obstacle con el robot (launch de bringup)

```bash
ros2 launch robotek_bringup open_challenge.launch.py direction:=cw gui:=true \
  params_file:=$PWD/src/robotek_open/config/open_v5.yaml \
  ackermann_steer_p_gain:=20 spawn_y:=-1.15 spawn_yaw:=3.141592653589793

ros2 launch robotek_bringup obstacle_challenge.launch.py direction:=cw gui:=true \
  ackermann_steer_p_gain:=20
```

Argumentos de ambos: `direction`, `gui`, `rviz`, `world`, `params_file`, `real_car` (por
defecto `true`: servo, motor y sensores del coche real), `actuator_model`, `steer_delay`,
`steer_rate`, `steer_tau`, `accel_max`, `audit_dir`, `spawn_x/y/yaw`. Obstacle suma `strategy`.
`real_car:=true` pasa `real_sensors:=true` al launch de Gazebo.

### 6.3 Rondas que se guardan (los runners)

Para cualquier prueba del challenge usa los runners: guardan `round.json`, el juez y
`rounds.jsonl` (ver [AGENTS.md](../AGENTS.md)). Una ronda Open con ventana:

```bash
bash src/robotek_evaluation/tools/run_gui_experiment.sh mac-nuevo-sq100-cw \
  --params-file src/robotek_open/config/open_v5.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction cw --controller-direction auto --spawn-x 0.0 --spawn-y -1.15 \
  --spawn-yaw 3.141592653589793 --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 \
  --launch-arg real_car:=true --real-time-factor 2
```

Para CCW: `--direction ccw --spawn-yaw 0.0`. Para iterar sin ventana añade `--no-gui` (en la Mac
usa `--real-time-factor 2`, no `0`). Obstacle:

```bash
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh --name mac-nuevo-obs-s0-cw \
  --direction cw --seed 0 --steer-p-gain 20 --real-time-factor 2
```

Set estándar de Open (12 rondas): `open_standard_suite.sh <etiqueta> <perfil.yaml> [args…]`.
Más detalle y cómo leer resultados: «Cómo correr el Open» en el [README](../README.md#cómo-correr-el-open).
**Las rondas con el robot nuevo son otro modelo**: no se comparan con las anteriores
(ver el [roadmap](roadmap-robot-nuevo.md#fase-9-registro-y-contexto)).

### 6.4 Ver la cámara y RViz

```bash
bash src/robotek_evaluation/tools/view_camera.sh        # deja Gazebo y RViz abiertos al inicio
```

`--rviz` en el runner (con `--no-gui`) abre RViz con `open_camera.rviz`. Con RViz usar ×1.

## 7. El robot en el repositorio

| Qué | Dónde |
|---|---|
| Medidas del coche (eje, vías, rueda, sensores) | [`robotek_common/vehicle.py`](../src/robotek_common/robotek_common/vehicle.py) |
| URDF/xacro (por defecto en todos los launch) | [`robotek_description/urdf/robotek.urdf.xacro`](../src/robotek_description/urdf/robotek.urdf.xacro) |
| Mallas del STEP (solo visuales) | [`robotek_description/meshes/`](../src/robotek_description/meshes) |
| Layout de la ventana de Gazebo | [`robotek_gazebo/config/gui_scene_only.config`](../src/robotek_gazebo/config/gui_scene_only.config) |
| Puente ROS–Gazebo | `robotek_gazebo/config/robotek_bridge.yaml` |

Medidas del 26 oct 2026 (`Assembly3.stp` con manguetas, placa de pivotes, bujes y ruedas, y el
calibrador del 20–21 oct): distancia entre ejes 118,83 mm (eje delantero en los pivotes del STEP,
trasero del calibrador), vía delantera 133,05 mm y trasera 123,5 mm, pivotes a 73,75 mm (cada uno
en el eje de su agujero de la placa base, con la mangueta pegada a la placa), rueda 61,0 mm de
diámetro y 14,5 mm de ancho, cara superior de la placa a 45,6 mm del suelo (el calibrador dio 45),
LiDAR a 127,3 mm (plano de escaneo a 27,6 mm del suelo) y cámara a 55,8 mm (centro de su placa a
142,2 mm) por delante de `base_link`. `base_link` está en el centro entre ejes, en el suelo.

Las mallas salen de `Assembly3.stp` (marco del STEP: mm, Y arriba, frente hacia −X). El xacro las
convierte a `base_link` con `step_mesh`: `x = mesh_x − X`, `y = Z`, `z = Y + mesh_z`
(`mesh_x` = 24,24 mm pone `base_link` entre los ejes; `mesh_z` = 35,49 mm, el suelo bajo las ruedas). Para cambiar una pieza: abrir el STEP en SolidCraft,
exportar el cuerpo a STL (mm) a `meshes/` y listarla en la macro. Una pieza que se mueve va en su
link y pasa a `step_mesh` el origen de ese link (`ox`, `oy`, `oz`): así entran la mangueta de
Hiwonder (en `front_*_steer_link`, que gira sobre el pivote real) y la rueda del equipo con su
silicona en las cuatro esquinas, más el buje hexagonal delante (en `*_wheel`); la placa de pivotes
va en `base_link`. Desde el 26 oct 2026 el `Assembly3.stp` de `~/Downloads` trae esas piezas
(manguetas, placa y bujes del STEP del MentorPi A1 que mandó Hiwonder; la rueda reconstruida del
STL del equipo). El **LiDAR no usa malla**:
se dibuja con una caja y un cilindro; un cuerpo en el plano de escaneo taparía sus propios
rayos (está dentro del rango mínimo de 0,03 m, así que tampoco los bloquea).

## 8. IMU del coche real (placa vertical)

La Raspberry y la RRC Lite van de canto. En el coche, `robot.launch.py` pasa la IMU por
`imu_adapter` antes de las estrategias (`/rrc/imu_raw` → `/robotek/imu`, marco del coche: x
adelante, y izquierda, z arriba). Los ejes se miden en el coche con
`ros2 run robotek_hardware imu_axes` y se copian a `robotek_hardware/config/robot.yaml`
(`imu_adapter`, `measured: true`). Mientras diga `measured: false` el adaptador avisa en el
arranque. En simulación no hace falta: Gazebo ya da la IMU en el marco del coche.

## 9. Problemas frecuentes

| Síntoma | Causa y arreglo |
|---|---|
| `create`/`parameter_bridge` mueren con código −6, rutas `/opt/homebrew/opt/ros2-jazzy/...` | `install/setup.sh` encadena Homebrew. `source tools/macos_env.sh`, recompilar y comprobar `grep -c homebrew install/setup.sh` = 0 |
| `gz sim` se cae al iniciar cámara y LiDAR | Falta `OGRE2_RESOURCE_PATH`; lo pone `macos_env.sh` |
| Cámara sin imágenes, `DIRECTION_FAULT` | Fast DDS; `macos_env.sh` usa Cyclone DDS |
| La ventana de Gazebo se cierra al arrancar | No hay servidor y GUI en un proceso en macOS; usa el launch, no `gz sim` a mano |
| `file exists` al redirigir a un log en zsh | `noclobber`; usa `>\|` |
| El coche choca sin motivo en el primer giro | Atraso del reloj ([simulacion-macos.md](simulacion-macos.md#problema-conocido-atraso-intermitente-del-reloj)) |
