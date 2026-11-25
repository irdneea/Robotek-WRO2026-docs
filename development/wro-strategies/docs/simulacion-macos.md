# Simular en macOS (RoboStack)

Probado el 9 de octubre de 2026 en un MacBook con **Apple M4 Pro** (14 núcleos) y macOS
Darwin 27, con el entorno RoboStack Jazzy `~/Projects/WRO/.mamba/jazzy` (Gazebo Harmonic
`gz-sim8` 8.10, OGRE-Next 2.3.3, `ros_gz` 1.0.23). Open `open_realcar_v4` en square100,
sin GUI, a **×2 del tiempo real**: **7/7 rondas válidas**, 30 puntos estimados por ronda,
32,7–33,2 s simulados desde Start, ~16,7 s de pared.

Solo se probó **Open**. **La ventana de Gazebo y RViz funcionan** a ×1 (rondas válidas,
ver abajo). El set estándar completo y Obstacle siguen sin comprobar en la Mac.

> Guía completa desde cero (crear el entorno, compilar, lanzar, problemas): [guia-inicio-macos-robostack.md](guia-inicio-macos-robostack.md). Desde el 21 oct 2026 `macos_env.sh` quita las variables del ROS de Homebrew y usa siempre `gz`, `ros2` y `colcon` de RoboStack; la ventana de Gazebo muestra solo la vista 3D por defecto.

## Preparar (una vez por terminal)

```bash
cd ~/Projects/WRO-Strategies
source tools/macos_env.sh               # otro entorno: source tools/macos_env.sh /ruta/al/env
colcon build --packages-ignore robotek_hardware   # la primera vez y tras cada cambio en src/
source tools/macos_env.sh               # de nuevo, para cargar install/
```

`robotek_hardware` es solo para el coche real y no hace falta en la Mac. El aviso
`ros2-argcomplete.zsh ... no such file` al cargar `install/setup.zsh` no afecta.

[`tools/macos_env.sh`](../tools/macos_env.sh) deja preparado:

| Variable | Por qué |
|---|---|
| `PATH`, `AMENT_PREFIX_PATH`, `CMAKE_PREFIX_PATH` | `micromamba activate` deja `AMENT_PREFIX_PATH` vacío ([robot-real-pi.md](robot-real-pi.md#ver-los-sensores-en-rviz-desde-la-mac-robostack)) |
| `OGRE2_RESOURCE_PATH=$ENV/lib/OGRE-Next` | **Imprescindible.** El paquete conda de gz-rendering trae la ruta de los plugins de OGRE rellenada con espacios: `dlopen` recibe solo el directorio, no encuentra el RenderSystem de Metal y `gz sim` se cae (segfault en `Ogre2RenderEngine::CreateRenderSystem`) cuando arrancan la cámara y el LiDAR. Con la variable carga Metal en la GPU (`Metal: selected "Apple M4 Pro"` en `~/.gz/rendering/ogre2.log`) |
| `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` | **Imprescindible.** Con Fast DDS (por defecto) las imágenes de 640×480 casi no llegan en macOS: 2 de ~80 en una prueba local. El datagrama UDP máximo de macOS es 9216 bytes. `FASTDDS_BUILTIN_TRANSPORTS=LARGE_DATA` dio 0. Sin imágenes la estrategia no decide el sentido (`DIRECTION_FAULT`) |
| `ROS_DOMAIN_ID=42`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` | La simulación no se mezcla con el coche (dominio 1) ni con otros equipos de la red |

Los runners (`run_gui_experiment.sh`, `run_obstacle_gui_experiment.sh`,
`view_camera.sh`) cargan `/opt/ros/jazzy/setup.bash` solo si existe. En Linux nada cambia;
en la Mac usan el entorno que dejó `macos_env.sh`.

## Una ronda

```bash
bash src/robotek_evaluation/tools/run_gui_experiment.sh mac-v5-sq100-cw \
  --params-file src/robotek_open/config/open_v5.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction cw --controller-direction auto --spawn-x 0.0 --spawn-y -1.15 \
  --spawn-yaw 3.141592653589793 --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 \
  --launch-arg real_car:=true --no-gui --real-time-factor 2
```

Para CCW: `--direction ccw --spawn-yaw 0.0`. El resto de variantes y cómo leer los
resultados están en «Cómo correr el Open» del [README](../README.md#cómo-correr-el-open).

**En la Mac usar `--real-time-factor 2`, no `0`.** En Linux `0` (sin límite) iba a
~1,8× y el resultado no cambiaba. El M4 Pro hace correr Gazebo hasta a ~6×, y los nodos
Python (estrategia, modelos de sensores y actuador) no le siguen el ritmo: quedan huecos
sin control y el coche choca.

| `--real-time-factor` | Rondas square100 | Válidas | Velocidad real | Hueco máx. de control | Atraso del reloj (mediana) |
|---|---|---|---|---|---|
| 1 | 5 (tras el periodo con atraso, ver abajo) | 5/5 | 1× | 0,11 s | 0,03 s |
| **2** | 7 (4 CW, 3 CCW) | **7/7** | **~2×** | **0,11 s** | **0,05 s** |
| 3 | 2 | 1/2 (CW: 27 puntos estimados) | 2,3–2,9× | 0,74 s | 0,08 s |
| 4 | 2 | 0/2 (choques) | 3,4–3,6× | 0,70 s | 1,2–1,4 s |
| 0 (sin límite) | 1 | 0/1 (choque) | ~6× | 0,82 s | — |

El periodo de control es 0,10 s; un hueco mayor significa ciclos de control perdidos.

## Comparación con Linux

Mismo perfil, campo, salida y juez. Square100 CW/CCW en la Mac: 32,7–33,2 s simulados.
En el set estándar v4-r1 de Linux: 33,416 s (CW) y 33,916 s (CCW)
([CW](open-challenge-runs/20261008T071317Z-std12-realcar-starts-v4-r1-square100-cw/round.json),
[CCW](open-challenge-runs/20261008T071231Z-std12-realcar-starts-v4-r1-square100-ccw/round.json)). Solo es una geometría y
pocas repeticiones con ruido. No mezclar estas rondas con las de Linux para elegir
mejores rondas: es otro contexto de ejecución.

## Problema conocido: atraso intermitente del reloj

Entre las 05:03 y las 05:21 (hora local) del 9 de octubre, **seis rondas a tiempo real
chocaron con la isla en el primer giro** (2–6 puntos estimados). El reloj de simulación
que veían los nodos ROS iba **1,0–1,5 s por detrás** de Gazebo. El atraso crecía durante
los primeros ~10 s y después se mantenía. La dirección reaccionaba ~0,3 s tarde, unos
38 cm a 1,28 m/s.

Lo que se comprobó:

- Un nodo Python mínimo que solo escuchaba `/clock` tenía el mismo atraso que la
  estrategia: el retraso venía de la entrega de `/clock`, no de la estrategia.
- **No eran las imágenes:** sin el puente de la cámara el atraso fue igual (1,46 s frente
  a 1,28 s). Usar `compressed` no lo resolvería.
- Un mundo vacío con solo el puente de `/clock` no tenía atraso.
- Desde las 05:24 **no volvió a aparecer** a ×1 ni a ×2, con la misma configuración:
  12 rondas sin atraso (5 a ×1, 7 a ×2). A ×4 sí aparece (1,2–1,4 s): los nodos no le
  siguen el ritmo a Gazebo.
- No se encontró la causa. Durante una ronda con atraso, `xprotectd` (antivirus de macOS)
  usaba ~1,1 núcleos; en las rondas buenas no aparecía. Encaja con que macOS revise los
  binarios recién compilados y los del entorno las primeras veces, pero no está
  demostrado. La máquina en total no estaba saturada (~25 % de la CPU).

**Si una ronda choca en el primer giro sin motivo aparente**, comprobar el atraso antes
de culpar a la estrategia: comparar `sim_time` de `telemetry.csv` con el reloj de Gazebo
(`gz topic -e -t /world/<mundo>/stats`) en el mismo instante. Con atraso de más de
~0,2 s, la ronda no sirve para evaluar la estrategia. Esperar unos minutos tras compilar
y repetir.

## Ventana de Gazebo

Con el comando normal, sin `--no-gui`. En macOS `gz sim` no puede llevar el servidor y la
ventana en el mismo proceso ([gz-sim#44](https://github.com/gazebosim/gz-sim/issues/44));
sin cambios, Gazebo se cerraba al arrancar (`20261009T115303Z-macos-gzgui-v4-sq100-cw`,
`INTERRUPTED.md`). Desde el 9 oct 2026 `robotek_sim.launch.py` lo detecta (`sys.platform ==
'darwin'`): arranca el servidor con `-s` y la ventana como proceso aparte (`gazebo_gui`,
`gz sim -g`). En Linux no cambia nada. El runner la cierra al terminar.

| Ronda | Cómo | Resultado |
|---|---|---|
| `20261009T115347Z-macos-gzgui-split-v4-sq100-cw` | `--no-gui` + `gz sim -g` a mano | Válida, 30 puntos, 32,697 s sim / 33,3 s pared |
| `20261009T115529Z-macos-gzgui-launch-v4-sq100-cw` | Comando normal, con el launch nuevo | Válida, 30 puntos, 32,596 s sim / 33,0 s pared |

Usa Metal en la GPU, como el servidor. El "Unable to load Ogre Plugin" del log es el
intento fallido previo a cargar Metal (ver `OGRE2_RESOURCE_PATH`), no un error real.
Obstacle usa el mismo launch, pero no se probó con ventana.

## RViz

`--no-gui --rviz` abre RViz con `open_camera.rviz` y Gazebo sin ventana. Probado a ×1 en
square100 CW (`20261009T114904Z-macos-rviz-v4-sq100-cw`): se vio bien, válida, 30 puntos
estimados, 32,896 s simulados / 33,3 s de pared, margen holgado. RViz usa OpenGL 2.1 (el
perfil de compatibilidad de macOS), sin avisos. Con RViz conviene ×1: no se probó a ×2.

## GPU

Gazebo renderiza con Metal en la GPU solo los sensores: cámara (640×480, 6 fps con
`real_car:=true`) y `gpu_lidar` (10 Hz). La física, el puente y todos los nodos corren en
la CPU. La carga de GPU es baja: 3–25 % durante una ronda, indistinguible del escritorio
con `ioreg`.

## Rondas de esta prueba

Todas en `docs/open-challenge-runs/20261009T*-macos-robostack-*` y en
[`rounds.jsonl`](open-challenge-runs/rounds.jsonl) con `platform: macos_robostack`.
Incluye los intentos fallidos mientras se encontraban los dos arreglos de entorno:

| Rondas | Qué se probaba | Resultado |
|---|---|---|
| `nogui-v4` | Sin `OGRE2_RESOURCE_PATH` | Gazebo se cae al iniciar los sensores (`not_started_or_missing_start`) |
| `nogui-metal-v4` | Metal, `--real-time-factor 0`, Fast DDS | Sin imágenes ni sensores a tiempo; sin puntos |
| `nogui-metal-camprobe*` | Ídem a ×1, inspeccionando la cámara | Fast DDS no entrega las imágenes: `DIRECTION_FAULT`, 0 puntos |
| `nogui-metal-cyclone-v4` | Cyclone, `--real-time-factor 0` | Huecos de hasta 6,9 s sin control; atascado, 0 puntos |
| `nogui-metal-cyclone-{rtf1,latprobe,clockprobe}`, `lagtest-A-camera`, `lagtest-B-nocamera` | ×1 durante el periodo con atraso; B sin puente de cámara | Choque en el primer giro, 2–6 puntos |
| `lagtest-D-clock2`, `lagtest-A2..A4`, `gpucheck` | ×1 sin atraso (D con un segundo puente de `/clock` para medir) | 5/5 válidas, 30 puntos, 32,7–33,1 s |
| `lagtest-R0-auto` | `--real-time-factor 0` sin atraso | Choque, 2 puntos |
| `rtf2-r1..r3`, `envscript-rtf2` | ×2; la última con `tools/macos_env.sh` y el runner `.sh` | 7/7 válidas, 30 puntos, 32,7–33,2 s |
| `rtf3-r1`, `rtf4-r1` | ×3 y ×4 | ×3: 1/2 válidas; ×4: 0/2 |

| `contactlog-rtf4` | Grabador de contactos por episodios, en vivo | Choque; 31.690 contactos en 21 KB |
| `watchfix-rtf4` | Vigilante del runner corregido, en vivo | Cortada por `no_section_progress_30s` a los 17 s de pared |

`lagtest-*` usan `--controller-direction cw` (sin detección de sentido) salvo `R0-auto`;
el resto, `auto`. En `rtf4-r1-…-cw` el runner no cortó a los 180 s simulados (llegó a
803 s) y el `contacts.jsonl` pesaba 249 MB. Las dos cosas ya están corregidas y también
afectaban a Linux: el vigilante del runner descartaba las filas de telemetría con comas
dentro de `turn_trigger`, y los contactos se guardaban uno por paso de física
([formato nuevo](juez-y-validacion.md#formato-de-contactsjsonl-episodios-9-oct-2026)).

## ROS de Homebrew (`idesign0/ros2`): no sirve por ahora

Probado el 9 oct 2026 con `ros2-jazzy` 26.07.31.106 (`/opt/homebrew/opt/ros2-jazzy`).
Se decidió seguir con RoboStack.

- Nuestro código compila con él: venv aparte con el Python 3.11 de python.org,
  `colcon` y `opencv-python-headless<5`, y `--cmake-args -DPython3_EXECUTABLE=<venv>`.
  Así no hace falta `brew unlink python`, como pide su README.
- `gz` es un script Ruby que usa `/usr/bin/ruby`; SIP le quita `DYLD_LIBRARY_PATH` y no
  carga Gazebo. Haría falta `brew install ruby`.
- **Bloqueante:** los binarios de Gazebo de la fórmula se compilaron con abseil
  `lts_20260107` y Homebrew ya instala `20260817`, así que `gz sim` no carga
  ([issue #3 del tap](https://github.com/idesign0/homebrew-ros2/issues/3), abierto).
  El mantenedor tiene pausadas las nuevas versiones. Compilar ROS + Gazebo desde
  `ros2_macOS` exige `brew unlink` de varias librerías y `sudo`, y lleva horas.
- Se puede volver a probar cuando el tap publique una versión nueva (`brew upgrade
  ros2-jazzy`).

## Pendiente

- Set estándar completo (`open_standard_suite.sh … --real-time-factor 2`) y Obstacle.
- Causa del atraso intermitente de `/clock`; registrar el atraso en cada ronda para
  descartar automáticamente las afectadas.
