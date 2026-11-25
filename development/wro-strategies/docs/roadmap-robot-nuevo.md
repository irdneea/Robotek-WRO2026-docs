# Roadmap: validar desde cero con el robot nuevo

21 de octubre de 2026. El URDF por defecto y `vehicle.py` ahora describen el coche **medido**
(calibrador y `Assembly3.stp`), no el modelo anterior. Todo lo que se validó con el modelo viejo
(rondas, perfiles, calibraciones) **hay que repetirlo**: es otro contexto de modelo. Esta lista
dice qué probar, en qué orden, con qué clases y qué comandos, y cuándo se da por bueno cada paso.

Cómo preparar la Mac y lanzar todo: [guia-inicio-macos-robostack.md](guia-inicio-macos-robostack.md).

## Orden de trabajo de documentación y simplificación (decidido el 21 oct 2026)

1. **Documentar el Open en `learn/`** tal como está hoy, con capturas reales de Gazebo y RViz ([fase 10, paso A](#fase-10-documentar-y-simplificar-el-open-en-este-orden)).
2. **Simplificar el Open** (menos estados y menos parámetros) sin cambiar sus resultados (paso B).
3. **Ajustar los documentos** a la versión simplificada (paso C).
4. **Solo entonces** documentar el Obstacle en `learn/` (paso D).

Las demás fases siguen en paralelo, pero ninguna guía de Obstacle se escribe antes de cerrar el paso C.

## Qué cambió respecto al modelo anterior

| Dato | Antes | Ahora | Dónde |
|---|---|---|---|
| Distancia entre ejes | 130 mm | **118,83 mm** (pivotes del STEP, 26 oct) | `vehicle.WHEELBASE`, URDF `wheel_base`, `robot.yaml` |
| Vía delantera / trasera | 100 / 100 mm | **133,05 / 123,5 mm** (delantera del STEP, 26 oct; pivotes a 73,75 mm) | `FRONT_TRACK`, `REAR_TRACK`, URDF |
| Rueda | Ø 60 × 12 mm | **Ø 61 × 14,5 mm** | `WHEEL_RADIUS`, `WHEEL_WIDTH` |
| Placa (colisión) | 177 mm centrada | **189 mm, centro 8,64 mm adelante** | URDF `chassis_len`, `chassis_x` |
| LiDAR | +60 mm, a 70 mm del suelo | **+127,3 mm, a 27,6 mm del suelo** | `LIDAR_OFFSET_X`, `lidar_joint` |
| Cámara | +70 mm, 83 mm de alto | **+55,8 mm, 142,2 mm de alto** | `CAMERA_OFFSET_X`, `camera_joint` (`real_sensors`) |
| `REAR_AXLE_X` | −65 mm | **−59,4 mm** | `vehicle.py` |
| `OUTLINE_HALF_WIDTH` / `_LENGTH` | 56 / 95 mm | **73,8 / 89,2 mm** | `vehicle.py` (largo real con LiDAR: ~232 mm, ver fase 6) |
| Visuales | cajas | piezas del STEP + colores del coche real | URDF, `meshes/` |
| Ventana de Gazebo | layout completo | **solo la vista 3D** | `gui_scene_only.config` |

## Riesgos conocidos (leer antes de conducir el coche real)

1. **El servo de dirección cambió de posición y giró 90°.** El centro (`servo_center_us`), el
   signo (`servo_sign`), las ganancias (`servo_gain_pos/neg`) y la tabla servo → ángulo de rueda
   (`wheel_table_*`, `wheel_limit_deg`) de `robot.yaml` son del montaje anterior: con otra palanca y
   otra posición de las varillas, 1500 µs ya puede no dejar las ruedas rectas y el mismo ángulo de
   servo da otro ángulo de rueda. `base_adapter` avisa mientras `servo_measured: false`. **Medir de
   nuevo antes de mover el coche** (fase 4). Los ángulos
   17,6° / 19,7° anteriores (`real_car_v1.yaml`, `REAL_STEER_LIMIT`) salieron de círculos
   medidos con `L = 0,13 m` (`ángulo = atan(L / R)`). Con `L = 0,1174 m` el mismo
   radio da un ángulo menor: 25° de servo → 17,9° (izq.) y 16,0° (der.), no 19,7° y 17,6°; el
   radio mínimo medido es 0,41 m. Con los valores viejos y el modelo nuevo, el simulador giraría
   más cerrado (0,37 m) que el coche. **Hasta recalcularlo (fase 4), no usar `robot.yaml` ni
   estos perfiles para conducir el coche real.**
2. **Alturas de LiDAR y cámara.** El LiDAR escanea a 30 mm del suelo (antes 70 mm) y la cámara
   está a 144,6 mm (antes 83 mm). Los perfiles y la calibración de cámara del 8 de octubre
   (`REAL_CAMERA_PITCH` 0,17 rad, `REAL_CAMERA_YAW` 0,077 rad, `REAL_CAMERA_HFOV` 1,164 rad) se
   midieron con la geometría vieja.
3. **El LiDAR queda 68 mm delante del eje delantero.** Los umbrales de distancia al frente
   (`turn_front_distance`, `corner_lookahead`, …) están en el marco del LiDAR y se afinaron con
   el LiDAR 68 mm más atrás: con el modelo nuevo el fin de la pared interior se ve ~6,8 cm antes.
4. **La IMU quedó en otros ejes.** La Raspberry y la RRC Lite van de canto (la placa de la IMU
   queda vertical), así que el giroscopio z ya no es el rumbo ni el eje y del acelerómetro es
   «adelante»: eso se midió con la placa plana el 8 oct. Las estrategias leen `angular_velocity.z`
   como velocidad de giro. El coche real ahora pasa la IMU por `imu_adapter`
   (`robotek_hardware`, parámetros en `robot.yaml`), pero los ejes de `robot.yaml` son los viejos y
   `measured: false`: **medirlos antes de cualquier prueba con el coche** (fase 3). La simulación
   no cambia: Gazebo ya entrega la IMU en el marco del coche.
5. **Dos pruebas siguen fallando por esto** (ver fase 2).

## Fase 0: entorno

- [ ] `source tools/macos_env.sh`; `command -v ros2 gz colcon` apuntan a RoboStack.
- [ ] `colcon build --packages-ignore robotek_hardware`; `grep -c homebrew install/setup.sh` = 0.
- [ ] `ros2 launch robotek_gazebo robotek_sim.launch.py field:=open real_sensors:=true` abre
  **solo la vista 3D** con el coche morado y el LiDAR al frente.

Hecho el 21 oct: los tres puntos, en esta Mac.

## Fase 1: geometría del modelo contra el coche

Clases y archivos: `robotek_common/vehicle.py`, `robotek_description/urdf/robotek.urdf.xacro`,
`robotek_description/meshes/`, `Assembly3.stp`.

- [ ] Medir otra vez entre ejes y vías **con el coche cargado** (batería, cables) y anotar
  diferencias > 1 mm. Hay 2,9 mm de diferencia entre el calibrador (117,4) y los agujeros del
  STEP (120,3); decidir cuál manda y dejarlo escrito en `vehicle.py`.
- [x] **Vía delantera**: manda el STEP, 135,05 mm (26 oct 2026: `Assembly3.stp` con las manguetas y bujes de Hiwonder y la rueda del equipo; el calibrador daba 133,5 mm).
- [ ] Altura del plano de escaneo del LiDAR y del centro de la lente de la cámara con el coche
  sobre la mesa; ajustar `lidar_joint` y `camera_joint` si difieren > 3 mm.
- [ ] Masa e inercias reales (`body_mass` 0,8 kg y `wheel_mass` 0,05 kg son estimaciones del
  modelo viejo). Pesar el coche y repartir; actualizar `base_link` y las ruedas.
- [ ] Caja de colisión del chasis: sigue siendo la del modelo viejo (30 mm de alto, 189 mm de
  largo). Decidir si la colisión debe cubrir también la caja y la Raspberry (afecta a los
  contactos con pilares) y actualizar el juez si cambia.
- [ ] Cámara: tilt real y rotación (`REAL_CAMERA_PITCH`, `REAL_CAMERA_YAW`) con el soporte
  actual; compararlos con el STEP (`camera_support.stl`).
- [ ] Buscar constantes duplicadas con las medidas viejas: `grep -rnE "0\.13|0\.065|0\.06\b|0\.0885|0\.095" src`.
  Ya se actualizaron `obstacle_parking`, `actuator_analysis`, `measure_actuator_latency` y
  `robot.yaml`; revisar `robotek_evaluation` (juez, auditores) y `docs/`.

## Fase 2: pruebas unitarias

```bash
PYTHONPATH=src/robotek_common:src/robotek_hardware:src/robotek_obstacle:src/robotek_open \
  python -m pytest -q -p no:launch_testing -p no:launch_ros \
  src/robotek_common src/robotek_hardware src/robotek_obstacle src/robotek_open
```

Estado: 99 pasan, 4 fallan.

- [ ] `test_distance_samples_are_accumulated_and_consumed_once` y
  `test_stale_sensors_brake_without_advancing_mission_state`: fallan igual con el modelo viejo
  (`'SimpleNamespace' object has no attribute '_state_sent'` en `OpenStrategyNode.on_scan`).
  Es un fallo del arnés de prueba, no de geometría; arreglar el `SimpleNamespace`.
- [ ] `test_lidar_endpoint_anticipation_and_rearming` (ccw y cw): **cambio real de
  comportamiento.** Con el coche en x = 0,38 m el LiDAR ya pasó el fin de la pared interior
  (x = 0,5 m) y `side_open` es `True`. Reescribir el escenario según el LiDAR y reajustar
  `corner_lookahead` con rondas (fase 5), no solo mover números.
- [ ] Agregar una prueba que fije las medidas del coche (`vehicle.py` y el URDF coinciden):
  renderizar el xacro, leer `lidar_joint`, `camera_joint`, vías y rueda, y compararlos con
  `vehicle.py`. Hoy solo lo dice un comentario.

## Fase 3: sensores en simulación contra el coche real

Clases: `robotek_evaluation/sim_scan_model.py` (caídas del LD19), `robotek_hardware/scan_adapter.py`
(recorte ±110°), `robotek_open/open_perception.OpenPerception`,
`robotek_obstacle/obstacle_perception` (`scan_clusters`, `color_blocks`, `associate`).

- [ ] LiDAR: con el robot a 1 m de una pared plana, comparar rango real y simulado; revisar
  que ningún rayo toque el propio coche (en la prueba del 21 oct, 0 de 306 por debajo de 0,33 m).
- [ ] Cámara: grabar una imagen real con un pilar rojo y otro verde a cada lado y compararla con
  la simulada (`view_camera.sh`). Recalibrar `REAL_CAMERA_HFOV`, `REAL_CAMERA_PITCH`,
  `REAL_CAMERA_YAW` (procedimiento del 8 oct: [robot-real-pi.md](robot-real-pi.md)).
- [ ] `obstacle_perception.associate` usa `CAMERA_OFFSET_X` y `LIDAR_OFFSET_X` para unir el
  rumbo de la cámara con los grupos del LiDAR: con la cámara 72 mm detrás del LiDAR el paralaje
  a 20–30 cm de un pilar es grande. Probar a 0,2 / 0,3 / 0,5 m con pilares.
- [ ] **IMU vertical (bloqueante para el coche real).** Con el coche quieto sobre la mesa y la pila
  parada: `ros2 run robotek_hardware imu_axes` (3 s quieto, luego un empujón suave hacia
  delante). Imprime el bloque `imu_adapter:` para `robot.yaml` y el error angular de cada eje
  (> 15° = placa inclinada o empujón torcido, repetir). Pegarlo en `robot.yaml` con
  `measured: true`. Comprobar a mano en `/robotek/imu`: girar el coche a la izquierda da
  `angular_velocity.z > 0`, en reposo `linear_acceleration.z ≈ +9,8` y un empujón hacia delante
  da `linear_acceleration.x > 0`.
- [ ] Actualizar `FORWARD_AXIS = 'ay'` en `actuator_analysis.py` (y el análisis de `imu.csv` de
  `actuator_test`, que guarda los ejes de la placa) con el eje de «adelante» medido.
- [ ] `imu_link` del URDF sigue en `(0, 0, 0,061)` y sin giro: el modelo de la RRC Lite no está
  en el STEP. Poner su posición real y comparar la aceleración centrípeta en círculos
  (fase 4). La simulación no necesita el giro: ya está en el marco del coche.

## Fase 4: actuadores y dirección

Archivos: `robotek_evaluation/config/real_car_v1.yaml`, `robotek_evaluation/sim_actuator_model.py`,
`robotek_hardware/config/robot.yaml`, `robotek_hardware/actuator_analysis.py`,
`robotek_bringup/launch/actuator_test.launch.py`, `tools/measure_actuator_latency.py`.

- [ ] **Calibrar el servo en el montaje nuevo (bloqueante).** Estático, con el coche sobre papel y
  solo la placa y el servo (sin motor):
  1. `ros2 launch rrc_lite_driver controller.launch.py` y, en otra terminal,
     `ros2 run robotek_hardware servo_steer`.
  2. Centro: `ros2 topic pub -r 5 /steer std_msgs/msg/Float32 "{data: 0.0}"`. Si las ruedas no quedan
     rectas, mover `servo_center_us` (±10 µs) hasta lograrlo. Subir de a poco: la palanca puede
     topar con la placa o las varillas con el eje.
  3. Signo: `data: 0.17` (10° a la izquierda). Si las ruedas giran a la derecha, invertir `servo_sign`.
  4. Tabla: para `data` = 0,17 / 0,26 / 0,35 / 0,44 rad (10°, 15°, 20°, 25°) y los mismos negativos,
     medir el ángulo de **cada** rueda delantera (transportador o foto desde arriba con regla) y
     anotar los µs que se publican. Rellenar `wheel_table_servo_deg`, `wheel_table_left_deg`,
     `wheel_table_right_deg` y `wheel_limit_deg` (el menor de los máximos de ambos lados, nunca
     más de 25°), y si hace falta `servo_gain_pos/neg` y `servo_min_us/max_us`.
  5. Poner `servo_measured: true` en `robot.yaml`, y los mismos límites en `real_car_v1.yaml`
     (`steer_limit`) y `REAL_STEER_LIMIT` de `vehicle.py` para que la simulación gire igual.

  Medir el ángulo de rueda directamente evita depender de `L`. Los círculos
  (`actuator_test.launch.py`) quedan para comprobar el radio mínimo después.
- [ ] Si se calibra con círculos: **recalcular los ángulos con `L = 0,1174`.** Conversión: `tan δ_nuevo = tan δ_viejo × 0,1174/0,13`.

  | Ángulo (viejo) | Ángulo (nuevo) |
  |---|---|
  | 8,6° / 8,7° | 7,78° / 7,87° |
  | 17,6° | 15,99° (`REAL_STEER_LIMIT` ≈ 0,279 rad) |
  | 19,7° | 17,92° |
  | 25° (límite de regla) | 22,84° |

  Actualizar `steer_limit` en `real_car_v1.yaml`, `REAL_STEER_LIMIT` en `vehicle.py` y las
  tablas de `base_adapter`. Mejor: repetir los círculos del coche con
  `actuator_test.launch.py` y analizarlos con `actuator_analysis.py` (ya usa `WHEELBASE = 0,1174`).
- [ ] Comprobar en Gazebo que 25° de servo da el radio mínimo medido en el coche (~0,41 m con el
  límite recalculado). Ver `sim_actuator_model` y el plugin `AckermannSteering` (`kingpin_width`
  = vía delantera, `wheel_separation` = vía trasera).
- [ ] Respuesta del servo y del motor (`steer_delay`, `steer_rate`, `steer_tau`, `drive_*`) no
  dependen de la geometría; confirmar con `measure_actuator_latency.py` que no cambiaron.
- [ ] Ganancia del plugin: `--ackermann-steer-p-gain 20` (Open) y `--steer-p-gain 20` (Obstacle).

## Fase 5: Open Challenge

Solo existe el **v5** (`robotek_open/v5/`: `Scene`, `OpenMission`, `OpenV5Node`); el v1–v4 se borraron el
26 oct 2026. Constantes de hardware: `open_constants.HARDWARE` (`wheelbase`, `lidar_offset_x`, … de `vehicle.py`).

1. [ ] Una ronda con ventana, `square100`, CW y CCW, perfil `open_v5.yaml`
   ([guía](guia-inicio-macos-robostack.md#63-rondas-que-se-guardan-los-runners)). Anotar los puntos y el tiempo:
   es la primera referencia del modelo del 26 oct 2026.
2. [ ] Mismos runs sin ventana y a ×2 (`--no-gui --real-time-factor 2`), 3 repeticiones con ruido
   (`--launch-arg sensor_noise:=true`).
3. [ ] Ajustar con el modelo nuevo los parámetros de `open_v5.yaml`. Un cambio por vez; registrar qué funcionó y
   qué no.
4. [ ] Set estándar de 12 rondas: `open_standard_suite.sh <etiqueta> src/robotek_open/config/<perfil>.yaml
   --ackermann-steer-p-gain 20 --launch-arg real_car:=true --real-time-factor 2` (o `tools/open_suite_quiet.sh`).
   Aprobar ≥ 10/12.
5. [ ] Registrar cada intento con `x`, `y` y `yaw` siempre explícitos.
6. [ ] Revisar `docs/open-challenge-runs/` y marcar el contexto de modelo nuevo (fase 9).

## Fase 6: Obstacle Challenge

Clases: `ObstacleMission`, `ObstacleDriver`, `BeamPlanner` (`obstacle_beam_planner`),
`ObstacleParking` y `Lot` (`obstacle_parking`), `LineDirection`, `scan_clusters`,
`color_blocks`, `associate` (`obstacle_perception`), `obstacle_field` (geometría del campo),
`obstacle_strategy_node`, `obstacle_detector_node`.

- [ ] **Decidir el largo del coche para el parqueo.** `LENGTH = 2 × OUTLINE_HALF_LENGTH` = 178 mm
  (ruedas) y `LOT_LENGTH = 1,5 × LENGTH`. El coche real mide ~232 mm con la pestaña del LiDAR
  (147 mm delante de `base_link`, 85 mm detrás). Leer la regla ([reglas generales](WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md))
  y fijar qué largo cuenta. Si es el total, `footprint()` ya no es simétrico respecto a
  `base_link` (la parte delantera llega 31 mm más lejos): hay que descentrar el rectángulo.
- [ ] `FRONT_AXLE_X`, `HALF_TRACK`, `WHEEL_RADIUS`, `WHEEL_HALF_WIDTH` de `obstacle_parking.py` ahora
  salen de `vehicle.py` (`WHEELBASE/2`, `FRONT_TRACK/2`, …). Verificar `REACH` y las ruedas
  delanteras que sobresalen con 22,8° de giro.
- [ ] `BeamPlanner` y `ObstacleDriver` usan `WHEELBASE` y `HALF_L`/`HALF_W`: volver a comprobar que
  la trayectoria predicha coincide con la real (comparar `telemetry.csv` con la pose auditada).
- [ ] Semillas 0–4 en ambos sentidos con `run_obstacle_gui_experiment.sh`, y `run_obstacle_batch.sh`
  para lotes; auditar con `src/robotek_evaluation/tools/audit_obstacle_runs.py`.
- [ ] Parqueo: `layout parking`; comprobar `PARKED` dentro del margen de 5 mm y que el coche no
  toque los límites (`LIMIT_THICKNESS`).

## Fase 7: arneses de equivalencia (si se toca código, no solo medidas)

```bash
python3 src/robotek_evaluation/tools/check_obstacle_refactor_equivalence.py
python3 src/robotek_evaluation/tools/check_open_refactor_equivalence.py
python3 src/robotek_evaluation/tools/check_open_sensor_equivalence.py
```

Estos arneses compararán contra el comportamiento previo: con las medidas nuevas los valores de
referencia cambian. Regenerarlos **solo** después de aceptar los cambios de las fases 4 a 6 y
documentar por qué. No mezclar con cambios de estrategia.

## Fase 8: pruebas de hardware en el coche (todas, en este orden)

Qué cambió físicamente en la construcción nueva y por qué obliga a repetir cada prueba:
ruedas y ejes (distancia entre ejes 117,4 mm, vías 133,5 / 123,5 mm, Ø 61 mm), **servo de dirección
movido y girado 90°**, **Raspberry Pi y RRC Lite de canto** (IMU en otros ejes), LiDAR 68 mm delante
del eje delantero y a 30 mm del suelo, cámara 72 mm detrás del LiDAR y a 144,6 mm, placa distinta
(189 × 90 mm, 3 mm), driver del motor en otro sitio y cableado nuevo. Antes de cada prueba: parar el
stack del equipo (`~/scripts/stop_ros.sh`) y cargar los dos workspaces
(`source ~/wro_controller_ws/install/setup.bash && source ~/Projects/WRO-Strategies/install/setup.bash`),
como en [robot-real-pi.md](robot-real-pi.md#flujo-push-en-el-mac-pull-en-el-pi). Los resultados salen en
`~/robotek-runs/<UTC>-<prueba>/` del Pi: copiar `summary.json` o `results.json` a
`docs/robot-real-pi/` y anotar la fecha, el estado de la batería y el montaje.

**Nada de las pruebas que mueven el coche hasta cerrar H5, H6 y H4.** Con las ruedas en el aire
(`wheels_in_air:=true`) o el coche levantado en la primera salida de cada prueba.

| # | Prueba | Cambio que la motiva | Herramienta | Se da por buena si |
|---|---|---|---|---|
| H0 | Revisión mecánica y fotos | todo | regla, calibrador, fotos de arriba y de lado | medidas de la [fase 1](#fase-1-geometría-del-modelo-contra-el-coche) anotadas; sin tornillos flojos, cables lejos de ruedas y varillas |
| H1 | Alimentación y batería | cableado nuevo, driver movido | `power_monitor`, `battery_guard` | sin subtensión (`get_throttled` = 0x0) con el motor al 30 % y 50 % |
| H2 | USB y nombres estables | placas de canto, cables nuevos | `tools/usb_stress_test.py`, `tools/pi_usb_map.sh` | IMU, LiDAR y cámara ≥ 90 % de su frecuencia, sin huecos > 0,1 s ni errores USB en 120 s |
| H3 | Placa RRC Lite completa | placa de canto | `rrc_test` (seguras y, con ruedas en el aire, las que mueven) | todas PASS o MANUAL ok |
| H4 | **Ejes de la IMU** | RRC Lite de canto | `imu_axes` + comprobación en `/robotek/imu` | error de eje < 15° y las tres comprobaciones de abajo |
| H5 | **Servo: centro, signo y tabla** | servo movido y girado 90° | `servo_steer` + `/steer` | ruedas rectas en 0; el signo correcto; tabla de ±10° a ±25° por rueda |
| H6 | Dirección mecánica | servo, palanca y varillas nuevos | a mano y con `servo_steer` | sin roce ni topes hasta ±25°; holgura < 1°; vuelve al centro con la misma lectura ±1° |
| H7 | Motor y driver | driver movido, batería, ruedas nuevas | `actuator_test test:=motor`, `motor_driver` | arranque y tabla % → m/s medidos con batería cargada; el pulso sin deriva a un lado |
| H8 | LiDAR | otra posición y altura | `lidar.launch.py` + RViz (`tools/macos_rviz_real.sh`) | `scan_adapter` con 0 rad adelante, zona ciega medida, ningún rayo de la propia carrocería dentro de ±110° |
| H9 | Cámara | otra posición, altura y soporte | `sensors.launch.py`, `obstacle_detector` | rumbo de pilares dentro de 3° respecto al LiDAR; colores HSV vigentes |
| H10 | Estado, botón y LEDs | placa de canto | `status_leds`, `start_button` | verde = listo; el botón arranca; rojo si falla un sensor |
| H11 | Geometría con el coche en marcha | medidas nuevas | `actuator_test test:=circle` y `test:=steer` | radio mínimo y ángulo real de rueda coherentes con la tabla de H5 |
| H12 | Peso, equilibrio y calor | todo de canto, piezas nuevas | báscula, `vcgencmd get_throttled`, `vcgencmd measure_temp` | masa anotada para el URDF; sin estrangulamiento térmico en 10 min de carga |
| H13 | Parada, atasco y recuperación | otra masa y ruedas | `/robotek/stop`, `stall_*` de `OpenConfig` | frena en la distancia esperada; el atasco se detecta y recupera |
| H14 | Integración en seco | todo | `robot.launch.py challenge:=open` | ver abajo |

### H0: revisión mecánica

1. Medir otra vez con calibrador: distancia entre ejes, vía delantera (con la dirección recta), vía
   trasera, diámetro y ancho de rueda, altura de la cara superior de la placa, y la posición del
   centro del LiDAR y de la lente de la cámara respecto al centro de la rueda delantera.
2. Fotos de arriba, de lado y de frente, con una regla a la vista (sirven para el STEP y para el URDF).
3. Cables: ninguno a menos de 10 mm de una rueda, una varilla o la palanca del servo; los conectores
   de la placa de canto sin tensión (vibran al rodar).

### H1: alimentación

```bash
ros2 run robotek_hardware power_monitor --ros-args -p duration:=30.0   # durante un pulso del motor
```

Con la batería cargada y a 7,0 V. Anotar el mínimo de la batería y de `EXT5V_V`; `get_throttled`
debe seguir en `0x0` (el bit 0 es subtensión ahora y el bit 16 que ocurrió desde el arranque). El
cableado y el driver cambiaron de sitio: era el origen de los reinicios del 8 de octubre
([robot-real-pi.md](robot-real-pi.md#motor-que-funcionaba-a-ratos-y-alimentación-8-oct-2026)).

### H2: USB y cámara

```bash
ssh user@192.168.0.10 'source /opt/ros/jazzy/setup.bash; export ROS_DOMAIN_ID=1; python3 - --seconds 120' \
  < tools/usb_stress_test.py
```

Con la placa, el LiDAR y la cámara en marcha. Los nombres estables de los USB están en
[robot-real-pi.md](robot-real-pi.md#los-usb-y-sus-nombres-estables-9-oct-2026): comprobar que siguen
iguales con las placas de canto.

### H3: placa RRC Lite

```bash
ros2 run rrc_lite_driver rrc_driver &
ros2 run robotek_hardware rrc_test                                       # solo las seguras
ros2 run robotek_hardware rrc_test --ros-args -p tests:="[all]" -p wheels_in_air:=true
```

Plan completo en [rrc-lite-pruebas.md](rrc-lite-pruebas.md). Para `imu` el coche debe estar quieto.
Resultado en `~/robotek-runs/<UTC>-rrc-test/results.json`.

### H4: ejes de la IMU (bloqueante)

1. `ros2 run robotek_hardware imu_axes`: 3 s quieto y un empujón suave hacia delante.
2. Copiar el bloque que imprime a `imu_adapter` de `robot.yaml` y poner `measured: true`.
3. Comprobar con `ros2 topic echo /robotek/imu --field angular_velocity` (y `linear_acceleration`):
   giro del coche a la **izquierda** a mano → `angular_velocity.z > 0`; en reposo
   `linear_acceleration.z ≈ +9,8`; empujón hacia delante → `linear_acceleration.x > 0`.
4. Con el coche quieto 10 s medir el sesgo del giroscopio z (era +0,006 rad/s) y el ruido (σ ≈ 0,0019 rad/s)
   para `real_sensors` del URDF.
5. Actualizar `FORWARD_AXIS` en `actuator_analysis.py`.

### H5: servo (bloqueante)

Procedimiento paso a paso en la [fase 4](#fase-4-actuadores-y-dirección). Resultado: `servo_center_us`,
`servo_sign`, `wheel_table_*`, `wheel_limit_deg` en `robot.yaml`, `servo_measured: true`.

### H6: dirección mecánica

Con el coche en el aire, mover el servo a mano y con `servo_steer` hasta ±25°: sin roce de la palanca
con la placa, sin que las varillas toquen el eje, y sin chasquidos del servo en los topes (si
`servo_min_us`/`servo_max_us` empujan contra un tope, acortarlos). Medir la holgura de cada rueda
tirando a mano, y repetir 0 → +25° → 0 diez veces: el centro debe volver al mismo ángulo ±1°.

### H7: motor y driver

```bash
ros2 launch robotek_bringup actuator_test.launch.py test:=motor motor:=robotek
```

Recorrer 15, 20 y 30 % en pulsos de 0,25 s y luego los tramos largos de la [tabla de velocidades](robot-real-pi.md#velocidad-de-crucero-por--8-oct-2026-pulsos-de-1-s-con-vuelta-atrás),
con la batería **cargada** (la tabla de octubre se midió con batería baja, 7,0–7,4 V).
Actualizar `motor_pct_per_mps`, `motor_min_pct` y `motor_max_pct` de `robot.yaml` y la tabla de
`real_car_v1.yaml`. Comprobar que `motor_driver` sigue levantando STBY y que el watchdog (0,3 s) frena.

### H8: LiDAR

1. `ros2 launch peripherals lidar.launch.py` y ver `/scan` en RViz desde el Mac
   (`bash tools/macos_rviz_real.sh`).
2. Con el coche a 0,5 m de una pared plana, rangos de frente y a ±45° y ±90°; deben coincidir con la
   distancia medida con regla (±1 cm, recordando que el LiDAR queda 128 mm delante de `base_link`).
3. Volver a medir la zona ciega: con la geometría nueva los rayos que dan en la carrocería ya no son
   los de antes (`fov_deg` 110 y `min_valid_range` 0,12 m de `robot.yaml` salen de la construcción
   anterior). Dejar el parámetro con la zona que da en el coche y comparar con la simulación
   (`real_sensors:=true`).
4. Altura del plano de escaneo con una pared baja (la cinta a 30 mm del suelo).

### H9: cámara

1. `ros2 launch peripherals sensors.launch.py` y una imagen con un pilar rojo y otro verde a cada
   lado a 0,3 / 0,5 / 1 m.
2. Medir el rumbo de cada pilar en la imagen contra el del LiDAR
   ([procedimiento del 8 oct](robot-real-pi.md#cámara-frente-a-lidar-asociación-y-alineación-de-la-cámara)).
   Con el soporte y la altura nuevos recalibrar `REAL_CAMERA_PITCH`, `REAL_CAMERA_YAW` y
   `REAL_CAMERA_HFOV` en `vehicle.py` y los mismos valores en la simulación.
3. Repetir los colores HSV con la luz del lugar de la prueba
   ([colores en el coche real](robot-real-pi.md#colores-hsv-en-el-coche-real)).

### H10 a H13: estado, geometría, calor y paradas

- **H10:** arrancar `robot.launch.py`; el LED verde marca que están el LiDAR, la IMU y la cámara;
  el botón de la placa lanza `/start`; quitar el cable de la cámara y ver el rojo.
- **H11:** `actuator_test test:=circle` a izquierda y derecha con ángulos fijos y comparar el radio y
  el ángulo con la tabla de H5. Anotar el radio mínimo; con las medidas nuevas se espera ≈ 0,37–0,41 m
  según la tabla.
- **H12:** pesar el coche con batería y repartir el peso adelante y atrás (dos básculas o el cálculo
  por apoyo); 10 min de carga con `vcgencmd measure_temp` y `get_throttled` cada 30 s, con la Raspberry
  de canto (el ventilador y el flujo de aire cambiaron).
- **H13:** `/robotek/stop` en marcha a 0,3 m/s: parada en ≤ 0,15 m; bloquear una rueda con la mano
  y comprobar que los parámetros `stall_*` de `OpenConfig` detectan y recuperan.

### H14: integración en seco y en el suelo

1. `ros2 launch robotek_bringup robot.launch.py challenge:=open` con las ruedas en el aire: ver que
   los comandos de dirección y velocidad coinciden con los de la simulación en el mismo escenario.
2. En el suelo, a baja velocidad, en una recta de 2 m con paredes: sin deriva y sin tocar.
3. Una vuelta de Open (v5, `open_v5.yaml`) a baja velocidad y luego la ronda completa; comparar con la
   simulación del mismo perfil (misma salida, mismo sentido) y guardar `telemetry.csv` y la imagen.
4. Obstacle: primero solo la percepción sin manejar ([detector de pilares](robot-real-pi.md#detector-de-pilares-en-el-coche-real-obstacle_detector)),
   luego una vuelta con pilares (`mode:=laps`) y por último el parqueo (`mode:=park`).

Cada prueba termina con una nota en `docs/robot-real-pi/` (fecha, batería, qué se encontró, qué se
cambió) y la actualización de los parámetros y del modelo. No mezclar rondas con montajes distintos.

## Fase 9: registro y contexto

- Cada ronda guarda `round.json` y se añade a `rounds.jsonl` del desafío (ver [AGENTS.md](../AGENTS.md)).
  Añadir al registro el campo de modelo: `robot_model: measured_20261021` (el modelo anterior es
  `legacy_20261008`) y no comparar entre modelos.
- Mantener el Markdown de la mejor ronda por modelo, con enlaces a la evidencia y a los parámetros
  ([mejor ronda](open-challenge-runs/best-realcar-open-round.md)); el historial de mejoras en
  [realcar-open-history.md](open-challenge-runs/realcar-open-history.md).
- Actualizar `docs/next-steps.md` y `docs/simulacion-coche-real.md` con las
  medidas nuevas cuando termine cada fase.

## Fase 10: documentar y simplificar el Open (en este orden)

Punto de partida medido el 21 oct 2026: `robotek_open` tiene 1 445 líneas (1 212 con código), la
máquina de estados `open_state_machine.py` tiene **11 estados, 15 transiciones y 57 condiciones**, y
`OpenConfig` tiene **56 parámetros** (el perfil v4 fija 32 y deja 24 por defecto). La ruta normal usa
7 estados; `DIRECTION_FAULT`, `STALLED`, `OPERATOR_STOP` y `RECOVER` son paradas o fallos.

### Paso A: documentar el Open en `learn/`

Guía `learn/03-open-strategy/` con el formato de [learn/02](../learn/02-sensors-rviz/README.md):
índice, pasos numerados, esquemas SVG en `img/`, solución completa, cómo probarla sin el coche y con
él, problemas frecuentes y glosario. Escrita sobre el código **actual**, sin simplificar.

- [x] Esquemas: de los sensores al `/cmd_vel`; la máquina de estados; el control en cascada
  (carril exterior → rumbo → dirección → Twist); cuándo se decide girar.
- [x] Pasos propuestos: 1 qué es el Open y cómo se puntúa; 2 qué recibe el coche (LiDAR, giroscopio,
  cámara) y por qué no hay odometría; 3 ver el campo y el coche en Gazebo; 4 ver lo que ve el coche
  en RViz; 5 la percepción (`OpenPerception`: distancias, eje de la pista, fin de la isla);
  6 el control (`OpenController`); 7 la máquina de estados (`OpenStateMachine`, `State`);
  8 la dirección de la vuelta con la cámara (`open_vision`); 9 una ronda de punta a punta y cómo leer
  `round.json`; 10 las pruebas sin el coche (`test_open_strategy.py`); 11 retos.
- [x] Capturas reales de **una ronda Open con ventana y RViz** (`run_gui_experiment.sh` sin `--no-gui`
  y con `--rviz`, a ×1): la ventana de Gazebo y la de RViz, con el identificador de ventana del
  sistema (`screencapture -l`), en `learn/03-open-strategy/img/`. Gazebo y RViz no son aplicaciones
  que computer use pueda controlar, por eso se capturan por ventana.
- [ ] Probar la guía de punta a punta en una terminal nueva ([guía de inicio](guia-inicio-macos-robostack.md)).

Hecho el 21 oct 2026 ([guía](../learn/03-open-strategy/README.md), commit `ffcc506`): 4 esquemas SVG, 4 capturas reales (2 de Gazebo y 2 de RViz de una ronda `square100` CCW, 30 puntos en 32,797 s), un mini control en `solution/` con 4 pruebas. Falta probar la guía de punta a punta en una terminal nueva.

### Paso B: simplificar el Open sin afectar sus resultados

**Estado (21 oct 2026):** hecho en lo que se podía sin cambiar resultados: 15 commits verificados.
Método, medidas, 15 hallazgos y las tres decisiones tomadas en
open-simplificacion-hallazgos.md. Quedó en 49 parámetros (antes 56),
8 estados (antes 11), un solo perfil, complejidad máxima por función 28 → 19 (11 sin el nodo) y una
observación inmutable entre percepción y máquina. El total de líneas no bajó (858 → 894 con el mismo
conteo). La verificación es `golden_open.py` (2 s) más el set estándar contra la dispersión de dos corridas
de referencia (`refac3-a`: 12/12 válidas, 30 puntos, media −0,03 s).

Objetivo: menos piezas que entender, mismo comportamiento. Es un **refactor**: no se mezcla con
cambios de estrategia ni de modelo, y se hace en commits pequeños, uno por cambio.

- [x] **Estados (hecho: 11 → 8, `STOPPED` con motivo; `RECOVER` sigue siendo estado):** reunir `DIRECTION_FAULT`, `STALLED`, `OPERATOR_STOP` y `DONE` en un solo
  `STOPPED` con un motivo (`reason`), y dejar `RECOVER` como parte de `FOLLOW` (un contador o
  subestado). Meta: de 11 a unos 6 estados, con las mismas salidas al mundo (`/robotek/state`, eventos
  de la telemetría y el estado final del juez).
- [ ] (parcial: 56 → 49) **Parámetros:** agrupar los 56 en 4 o 5 bloques (conducción, giro, final, visión, atasco), con
  valores por defecto razonables, y exponer como parámetro de ROS solo los que de verdad se ajustan
  (meta: 15 a 20). Los demás pasan a constantes del perfil. Los perfiles YAML antiguos siguen
  funcionando o se migran con una tabla.
- [x] **Condiciones de `step()`:** extraer las condiciones de girar y de terminar a funciones con
  nombre y prueba propia (hoy son 57 `if`/`elif` en una sola clase).
- [ ] **No tocar** la lógica de percepción ni el control salvo que el arnés pruebe que no cambia.

Cómo se verifica que no cambió nada (todas con el modelo nuevo, el mismo perfil v4 y el mismo límite de dirección):

1. `python3 src/robotek_evaluation/tools/check_open_refactor_equivalence.py` y
   `check_open_sensor_equivalence.py` (ver [AGENTS.md](../AGENTS.md)): regenerar la referencia
   **antes** del primer cambio y compararla después de cada commit.
2. Pruebas unitarias: las 107 que pasan hoy deben seguir pasando; las 2 de `lidar_endpoint_anticipation`
   siguen fallando por lo mismo hasta la fase 5.
3. Mismo set estándar de 12 rondas (`open_standard_suite.sh`, mismo perfil y banderas): 12/12 válidas
   con 30 puntos y tiempos dentro del rango de dos corridas de referencia más 1,0 s
   (`tools/compare_open_suites.py`; dos corridas idénticas difieren hasta 1,0 s por el ruido de sensores).
4. Dos rondas con ventana y con RViz (`square100` CW y CCW) antes de dar el cambio por cerrado.
5. Si alguna ronda cambia, se revierte ese commit y se anota en el historial; no se acepta «casi igual».

Plan de seguimiento (no es parte de A–D): [open-reimpl-v5.md](open-reimpl-v5.md), reimplementar el Open desde cero
con el mínimo de estados y código, con las ablaciones del v4 como evidencia.

### Paso C: ajustar los documentos al Open simplificado

- [x] `learn/03-open-strategy/` (esquemas, nombres de estados y de parámetros, capturas si cambia algo visible).
- [x] (hecho: estrategia §3.1, `guia-correr-open-v4.md`; `open-refactor.md` y `perfiles.md` ya llevan nota histórica) robotek-open-challenge-strategy.md (§3.1 máquina de estados, §4 perfiles),
  open-refactor.md, guia-correr-open-v4.md y perfiles.md.
- [x] Este roadmap (cuenta de estados y parámetros) y el glosario de `learn/`.
- [ ] Una línea en cada commit sobre qué se simplificó y con qué arnés se comprobó.

### Paso D: documentar el Obstacle en `learn/` (solo después del paso C)

Guías siguientes (`learn/04-…`) con el mismo formato y capturas de Gazebo y RViz de una ronda de
Obstacle. Esquema a confirmar con el equipo antes de empezar:

- [ ] Percepción de pilares (`scan_clusters`, `color_blocks`, `associate`, `SeatMap`).
- [ ] Localización y mapa (`Localizer`, `obstacle_field`).
- [ ] Planificación (`BeamPlanner`) y la regla del lado de rojo y verde.
- [ ] Misión y vueltas (`ObstacleMission`, `ObstacleDriver`).
- [ ] Estacionamiento (`ObstacleParking`, `Lot`).

Antes del paso D, revisar si el Obstacle tiene el mismo problema de estados y parámetros
(`obstacle_config.py` tiene 121 líneas) y decidir si se simplifica antes o después de documentarlo.

## Dónde buscar qué

| Tarea | Clase o archivo |
|---|---|
| Medidas del coche | `robotek_common/vehicle.py` |
| URDF, sensores, ruedas, mallas | `robotek_description/urdf/robotek.urdf.xacro`, `meshes/` |
| Mundos, puente, ventana | `robotek_gazebo/` (`robotek_sim.launch.py`, `config/gui_scene_only.config`) |
| Estrategia Open | `OpenConfig`, `OpenController`, `OpenPerception`, `OpenStateMachine`, `OpenStrategyNode` |
| Estrategia Obstacle | `ObstacleMission`, `ObstacleDriver`, `BeamPlanner`, `ObstacleParking`, `scan_clusters`, `associate` |
| Modelos de sensores y actuadores en sim | `sim_scan_model.py`, `sim_actuator_model.py`, `real_car_v1.yaml` |
| Juez y reportes | `rule_judge.py`, `open_round_report.py`, `obstacle_full_round_report.py` |
| Runners | `run_gui_experiment.sh`, `run_obstacle_gui_experiment.sh`, `open_standard_suite.sh`, `run_obstacle_batch.sh` |
| Coche real | `robotek_hardware` (`base_adapter`, `scan_adapter`, `imu_adapter`, `imu_axes`, `actuator_analysis`), `robotek_bringup/launch/robot.launch.py` |
