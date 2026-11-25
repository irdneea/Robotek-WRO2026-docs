# Guía «Construye la estrategia del Obstacle»: especificación (25 oct 2026)

Versión 1 de la guía del Obstacle, con el mismo formato que la del Open: un curso en el repo público
`~/Projects/robotek-learn` (andamiaje en `main`, solución de referencia en la rama `solutions-obstacle`
con una etiqueta `obstacle-step-N` por paso) y las páginas en `~/Projects/Portfolio-Astro`
(`/learn/obstacle-strategy/`). El usuario pidió tenerla ya; el v2 se seguirá mejorando una semana, así
que esta versión enseña el v2 tal como está (commit `b0137a9` de WRO-Strategies) y lo dice con
honestidad en el paso 9.

**Reglas comunes:** código e identificadores en inglés, prosa en español. Sin coautoría de IA en los
commits. No hacer push de ningún repo (lo decide el usuario). Simulación honesta: la estrategia del
lector solo recibe LiDAR, giroscopio y cámara. No copiar al repo público rutas `/home/user`, ni datos
del Pi, ni la textura WRO. El código viene de `WRO-Strategies/src/robotek_obstacle/robotek_obstacle/v2/`
(y de `obstacle_field.py`, `obstacle_localizer.py`, `obstacle_perception.py`, `obstacle_parking.py`) y
de `robotek_evaluation` (juez, laboratorio, generador del campo); es del mismo autor y se publica con
la licencia MIT del repo.

## 1. Lo que ve el lector (pasos)

| Orden | Slug | Título | Etiqueta | Módulos de la solución |
|---:|---|---|---|---|
| 0 | `paso-0-preparar` | Preparar el paquete | `obstacle-step-0` | (lo que imprime `ros2 pkg create`) |
| 1 | `paso-1-el-campo` | El campo y las reglas | `obstacle-step-1` | `lane.py` |
| 2 | `paso-2-ubicarse` | Ubicarse con los muros | `obstacle-step-2` | `localizer.py` |
| 3 | `paso-3-ver-las-senales` | Ver las señales y recordarlas | `obstacle-step-3` | `signs.py` |
| 4 | `paso-4-la-linea` | La línea: un lado por señal | `obstacle-step-4` | `plan.py` |
| 5 | `paso-5-las-esquinas` | Las esquinas: recta, arco, recta | `obstacle-step-5` | `corner.py` |
| 6 | `paso-6-seguir-la-linea` | Seguir la línea | `obstacle-step-6` | `follow.py` |
| 7 | `paso-7-la-mision` | La misión: salir, mirar, tres vueltas | `obstacle-step-7` | `mission.py`, `strategy.py` |
| 8 | `paso-8-aparcar` | Aparcar en paralelo | `obstacle-step-8` | `park.py` |
| 9 | `paso-9-puntuar-y-medir` | Puntuar y medir | `obstacle-step-9` | `RESULTADOS.md` |

`drive.py` (el nodo) existe desde el paso 2 y crece con los pasos, como en el Open.

## 2. `robotek-learn`, rama `main` (trabajador A)

Nuevo, sin romper nada del Open:

- `src/robotek_course/robotek_course/obstacle_base.py`: `ObstacleStrategyBase`, la clase base del
  curso para el Obstacle (sin ROS), análoga a `StrategyBase`:
  - `on_scan(scan)`: usa cada marca de tiempo una vez (odometría LiDAR una vez por marca), guarda
    `self.scan`, `self.scan_stamp` (s), `self.new_scan`; el primer escaneo es Start si `auto_start`.
  - `on_imu(now, gyro_z)`: `self.gyro`; integra `self.yaw += (gyro - self.gyro_bias) * dt` (el
    lector fija `gyro_bias` al calibrar).
  - `on_signs(observations, stamp)`: lista de `dict(x, y, color)` en el sistema del coche (x delante,
    y izquierda, m; color `'red'`/`'green'`) que da la asociación cámara + LiDAR; guarda
    `self.signs`, `self.signs_stamp`.
  - `control(now, dt) -> (speed, steer)`: lee `self.travelled` de la odometría, llama a
    `update(now, dt)` (lo escribe el lector), pasa la velocidad a la odometría. Atributos de lectura:
    `label`, `done`, `parked`.
- `src/robotek_course/robotek_course/obstacle_vision.py`: `color_blocks(bgr, hfov, pitch, yaw)`,
  `scan_clusters(scan)`, `associate(blocks, clusters)` (de `obstacle_perception.py`).
- `src/robotek_course/robotek_course/obstacle_field.py`: el campo por las reglas:
  `regulation_signs(seed, parking=False)` (36 cartas, señal única, señales de la sección de salida a la
  fila interior con aparcamiento), `PARKING_LOT`, `build_world(directory, seed, parking)` que escribe
  `world.sdf` (campo + señales 50×50×100 mm rojo/verde + topes magenta + sensores de contacto + publicador
  de pose de las señales) y `manifest.json` (dirección, señales, `parking_lot`, `spawn_progress`).
  Plantillas SDF en `robotek_gazebo` si hacen falta (sin la textura WRO; el tapete propio ya existe).
- `src/robotek_course/launch/obstacle_round.launch.py`:
  `ros2 launch robotek_course obstacle_round.launch.py strategy:=my_obstacle seed:=0 direction:=ccw parking:=true gui:=true`.
  Genera el campo en la carpeta de la ronda (`~/robotek_runs/<fecha>-<nombre>/`), arranca el simulador
  (`sim.launch.py` con ese mundo y `real_car`), el nodo del lector (`<strategy>/drive`, remapeado como en
  el Open a `/cmd_vel_raw`), el árbitro y los registradores (pose real, pose de señales, contactos). El
  árbitro publica `/start`, termina la ronda a los 180 s o tras la parada final, e imprime la puntuación.
- `src/robotek_evaluation/robotek_evaluation/obstacle_judge.py` (+ geometría de auditoría que haga
  falta): el juez de `obstacle_full_round_report.py` con aparcamiento (`obstacle_parking_report.py`):
  vueltas, lados, señales movidas, parada, aparcamiento (15/7), máximo 55 en este alcance.
- `src/robotek_evaluation/robotek_evaluation/obstacle_lab.py`: el laboratorio rápido (del de
  WRO-Strategies, con la cámara real) que acepta `--strategy my_obstacle.strategy:Strategy` (una
  subclase de `ObstacleStrategyBase`), `--seed`, `--layout`, `--direction`, `--parking`, y un modo
  lote `--layouts 0-4 --seeds 0-4 --workers N` como `tools/obstacle_lab_suite.py`.
- `ros2 run robotek_course score_obstacle [carpeta]`: puntúa una ronda grabada.
- `course/obstacle/verify_step.py N` (comprobación en Gazebo sin ventana, como `verify_step.py`).
- README: sección «El reto Obstacle» con los comandos.
- Pruebas propias de la infraestructura (`src/robotek_course/test/`, `src/robotek_evaluation/test/`).

## 3. Solución de referencia y pruebas por paso (trabajador B)

- Paquete `src/my_obstacle` (ignorado en `main`, como `my_open`): `ament_python`, nodo `drive`.
  Módulos de la tabla del §1, portados del v2 a la clase base del curso:
  - `lane.py`: `INNER`, `OUTER`, `UNITS_PER_LAP`, `lane_pose`, `lane_normal`, `progress_of`, `advance`,
    `track_s`, `unwrap_s`, `SEATS` (asientos: progreso 2k, 2k+0,5, 2k+1; filas ±0,1 m).
  - `localizer.py`: `Localizer` (ajuste a muros + predicción), `direction_from_scan`, `scan_points`.
  - `signs.py`: `SeatMemory` (archivar clústeres por asiento, votos de color, `next_sign`).
  - `plan.py`: `side_offset`, `plan_knots`, `offset_at`, la vista previa (`lookouts`).
  - `corner.py`: el de v2 (`path`, `clearance`, `plan`, `knots`).
  - `follow.py`: `reference`, `steer` (anticipación de curvatura + realimentación lateral y de rumbo).
  - `mission.py`: SETUP/RUN/PARK/STOP, salida con retroceso, mirar señales desconocidas, tres vueltas.
  - `strategy.py`: `Strategy(ObstacleStrategyBase)`, une todo en `update`.
  - `park.py`: aproximación, plan A* (traer `search`/`Lot`/`move` de `obstacle_parking.py` al paquete
    o a `robotek_course`; decidir uno y documentarlo), maniobras.
- `course/tests/obstacle/test_step_N.py` (pytest puro, sin ROS) por paso, rojo → verde contra el
  esqueleto; `conftest.py` que importe `my_obstacle` desde `src/my_obstacle`.
- `course/maintainers/build_obstacle_solutions.py`: reconstruye la rama `solutions-obstacle` (un
  commit y una etiqueta `obstacle-step-N` por paso, como `build_solutions.py`).
- `RESULTADOS.md` del paso 9: tabla de rondas medidas en el laboratorio del curso (y en Gazebo si da
  tiempo) con puntos y tiempos, y los límites conocidos (abajo).

## 4. Páginas en Portfolio-Astro (trabajador C)

- Generalizar `src/lib/learn.ts` y las páginas para varias guías (hoy `GUIDE_ID` fijo): rutas
  `src/pages/learn/obstacle-strategy/index.astro` y `[step].astro` (copiar las de open-strategy con
  el id de la guía), y que `/learn` liste las dos.
- `src/content/learn/guides/obstacle-strategy.md` (order 2, repo `https://github.com/coach/robotek-learn`).
- `src/content/learn/steps/obstacle-strategy/paso-N-*.md` con el frontmatter del §1 (`tag`,
  `compareFrom`). Mismo estilo que los pasos del Open: «Lo que vas a ver», «La idea» (con números
  medidos), «Escríbelo» (qué funciones, firmas, pruebas `pytest course/tests/obstacle/test_step_N.py`),
  «Pruébalo en Gazebo» (comandos), «Si algo falla».
- Figuras SVG propias en `public/learn/obstacle/` (campo con asientos y filas, línea por señal, esquina
  recta-arco-recta, maniobra de aparcamiento). Widgets interactivos solo si sobra tiempo.
- Verificar con el servidor de desarrollo (`.claude/launch.json` del portfolio) y `astro build`.

## 5. Números del v2 para la guía (medidos, WRO-Strategies)

- Laboratorio sin aparcamiento, layouts 0–49 × CCW/CW (100 campos, semilla 0): **88/100 válidas**.
- Laboratorio con aparcamiento, layouts 0–9 × CCW/CW: **11/20 rondas con 55 puntos**.
- Gazebo (coche real, sin ventana, RTF 2): `reg4-ccw` sin aparcamiento **40 puntos, válida, 115,6 s**;
  con aparcamiento: vueltas bien (37) pero el aparcamiento no terminó en 180 s (la búsqueda de
  correcciones bloquea el bucle de control unos segundos).
- Límites conocidos: la esquina verde-interior → roja-exterior deja solo 3,4 cm de margen ideal; en CW
  la cámara (girada 4,4° a la izquierda) ve hasta 28,9° del lado de la isla (de ahí «mirar» las señales
  desconocidas); el aparcamiento tarda 35–70 s.
- Medidas del coche: `robotek_common/vehicle.py` (distancia entre ejes 117,4 mm, contorno 147,7 mm
  delante / 85,2 mm detrás / 74 mm de medio ancho, dirección 17,6°, cámara 66,7° girada 4,4°).
