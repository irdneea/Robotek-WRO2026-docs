# Open v5: simplificación con el lab realista (12 nov 2026)

Pedido del entrenador: bajar la complejidad del v5 y sus parámetros probando en el lab con muchos centros de mapa.

## Cómo se midió

- **Campos:** suite `centres` de `open_lab`, las 16 islas que permiten las reglas (cada lado con pasillo de 1,0 o
  0,6 m; `tools/make_open_centres.py` → `docs/open-challenge-runs/field-size-driver/worlds-centres/c<E><N><O><S>.sdf`,
  `W` = ancho, `N` = estrecho), en los dos sentidos: 32 rondas por semilla.
- **Coche:** `real_v4` (el coche del 11 nov, motor nuevo) con los valores de `car_picam.yaml` de robotek-learn.
- **Huecos del LiDAR:** `--car-param scan_gap_rate=0.68 --car-param scan_gap_max=0.5`, lo medido en el coche el
  11 nov. Sin huecos el coche no choca nunca en el lab. Con huecos choca más o menos como el coche real ese día:
  contra el muro exterior, en las curvas.
- **El lab copia ahora el freno del nodo** cuando el LiDAR se atrasa (`V5Strategy.SCAN_MAX_AGE`). Antes no lo
  modelaba.
- **«Buena»:** 24 secciones, 3 vueltas, sin contacto y parada dentro de la sección final. La parada del juez
  («judge-valid») falla mucho en el lab por una deriva de 2–3 mm después de DONE, con un tope de 2 mm. En el coche, el
  reset de la placa en DONE corta el motor, así que esa cifra no se usó para decidir.
- 5 semillas para las variantes y 10 para el resultado final. Ruido entre variantes: unos ±4 %.

## Resultados

| Variante (coche, 16 islas × 2 sentidos) | Con huecos | Sin huecos | Tiempo |
|---|---|---|---|
| Código del 11 nov con el freno del nodo (0,35 s; 0,6 s en curva; sin integrar el giroscopio en el hueco), 5 semillas | 46 % | 100 % | 38,4 s |
| … integrando el giroscopio durante el hueco | 68 % | 100 % | 38,5 s |
| … y un solo límite de 1 s en vez de 0,35/0,6 s | 76 % | 100 % | 38,3 s |
| … y estima de la pared de enfrente entre escaneos (código viejo + estos tres cambios), 10 semillas | 78 % | 100 % | 38,4 s |
| **Código simplificado (este), 10 semillas** | **79 %** (253/320) | **100 %** (320/320) | **37,6 s** |
| Simplificado con `corner_speed` 0,58 en vez de 0,64, 10 semillas | 89 % | 100 % | 39,9 s |

Gazebo (`real_v1`, set std12, 5 semillas): el código viejo con `open_v5.yaml`, 60/60 válidas en 40,7 s; el
simplificado con `corner_speed` 1,0, 60/60 válidas en 41,9 s. No se ha corrido en Gazebo de verdad ni con GUI.

### Qué se quitó y por qué (cada fila, 5 semillas con huecos)

| Quitado | Con huecos | Decisión |
|---|---|---|
| `lateral_kd` (derivada y su filtro paso bajo) | 85 % vs 82 % | Fuera. La recta es solo P (`lateral_kp`). |
| `lookahead_cap` | 84 % | Fuera el parámetro. El tope (distancia a la isla − 8 cm) queda fijo: sin él, en Gazebo (`inner_gap` 0,25) choca con la isla en la curva 4. En el coche (`inner_gap` 0,5) no actúa nunca. |
| `last_corner_speed` (todas las curvas a `corner_speed`) | 81 % | Fuera. En Gazebo la curva por defecto pasa a 1,0 m/s: antes eran 1,28 m/s en las curvas y 0,6 en la última. |
| Ritmo del arco a la velocidad de crucero | 82 % | Fuera. El arco usa `corner_speed`. |
| Tabla `REAL_SPEED` (motor viejo, 8 oct) | 81 % | Fuera. La rampa del arco usa `corner_speed` tal cual. |
| `LAST_TOLERANCE` 0,4 en la última curva | 82 % | Fuera. Una sola tolerancia, `turn_tolerance`, 0,3 por defecto. |
| `turn_delay_distance` | (0 en todos los perfiles) | Fuera. |
| `turn_scan_max_age` (nodo del coche) | 76 % vs 68 % | Fuera. Un solo `scan_max_age` de 1,0 s en el coche. |

### Qué se probó y se queda

| Probado | Resultado | Por qué se queda |
|---|---|---|
| `corner_speed` = crucero | **39 %** | Frenar antes de la curva es lo que más importa. |
| `brake_margin` 0,15 | 74 % | Se queda en 0,35 en el coche. |
| `turn_tolerance` 0,12 | 79 % | Se queda en 0,30. |
| `wall_heading_gain` 0 | 82 % (igual) | El lab no modela el error de escala del giroscopio que corrige (4–6° por curva en el coche, 4 nov). |
| `CONFIRMATIONS` 1 | 80 % con huecos, **94 %** sin huecos | Se queda en 2. |

### Qué se añadió (es poco)

- **Estima de la pared de enfrente** entre escaneos (`OpenMission.front`): la del último escaneo menos la velocidad
  mandada por el tiempo pasado desde entonces. Se usa para decidir el giro y para frenar. Con un hueco de 0,5 s el giro
  ya no empieza 0,4 m tarde.
- **Nodo:** en un hueco del LiDAR la misión sigue avanzando (se integra el giroscopio) y solo se anula la orden. Si el
  que falla es el IMU, el nodo no avanza la misión.

## Límites

- Quedan un 21 % de rondas con choque cuando hay huecos, casi todas contra el muro exterior en TURN. Bajar
  `corner_speed` a 0,58 baja los choques a la mitad, pero cuesta 2,3 s por ronda. Esa decisión es del entrenador.
- El lab no modela el servo que se congela (choques de las 17:59 y las 18:01 del 11 nov) ni los cuelgues de la placa.
- Los parámetros de Gazebo (`open_v5.yaml`) cambiaron (`corner_speed` 1,0): falta el set estándar en Gazebo con GUI.
- Comandos: `python3 tools/make_open_centres.py` y
  `python3 -m robotek_evaluation.open_lab --suite centres --car real_v4 --car-param scan_gap_rate=0.68 --car-param scan_gap_max=0.5 --param=...`.

## Segunda pasada (12 nov 2026, grupo 1)

Misma medida (16 islas × 2 sentidos × 10 semillas con los valores del coche, y el set std12 del modelo de Gazebo).

| Cambio | Con huecos | Sin huecos | Gazebo std12 |
|---|---|---|---|
| Referencia (primera pasada) | 79 % | 320/320, 36,95 s | 60/60, 41,92 s |
| Distancia recorrida = velocidad mandada × tiempo (sin `LidarOdometry` en el Open) | 80 % | 320/320, 36,95 s | 60/60, 41,92 s |
| Arco a giro completo hasta `turn_tolerance` (sin referencia en rampa ni adelanto) | 79 % | 320/320, 36,91 s | 60/60, 41,92 s |
| Rearme de la curva solo por distancia (`ARM_DISTANCE`), sin «volver a ver la isla» | 80 % | 320/320, 36,95 s | 60/60, 41,92 s |
| Rearme solo por «volver a ver la isla», sin distancia | 77 % | 320/320 | 60/60 |
| **Los tres primeros juntos (el código actual)** | **80 %** (255/320) | **320/320, 36,92 s** | **60/60, 41,92 s** |

- `mission.step` ya no recibe la distancia: `step(dt, scene, gyro_z, camera)`. El nodo y el lab no usan `LidarOdometry`
  (el Obstacle sí). En la telemetría, `distance_source` es `command` y las columnas `lidar_odom_*` quedan vacías.
- Salen `EXIT_ANGLE`, la referencia `ref` y el estado `armed`. `finish_stop_wait`, `calibrate_seconds` y
  `direction_fallback_wait` pasan a constantes (nadie los cambiaba).
- `mission.py`: 296 → 285 líneas; el Open deja de ejecutar el ajuste de escaneos (116 líneas) en cada vuelta del LiDAR.
- Pendiente (grupos 2 y 3 del plan): una sola forma de ver el fin de la isla, el rumbo por las paredes con la recta
  de la isla, el sentido sin cámara y sacar los dibujos de RViz del nodo.

## Tercera pasada (12 nov 2026, grupo 2)

El lab modela ahora el error del giroscopio del coche (`--car-param gyro_scale=0.94`: mide el 94 % del giro real,
los 4–6° por curva del 4 nov).

| Cambio (coche, 16 islas × 2 sentidos × 10 semillas) | Con huecos | Sin huecos | Gazebo std12 |
|---|---|---|---|
| Fin de la isla solo por «el lado se abre» | 45 % | 320/320 pero 39,9 s (+3 s) | 60/60, 43,4 s (+1,5 s) |
| Fin de la isla solo mirando adelante | 5 % | 320/320 | **0/60** |
| Sin corrección de rumbo por paredes, giroscopio al 94 % | 0 % | **0/320** | — |
| Corrección con dos rectas (una por lado), giroscopio al 94 % | 74 % | 320/320, 37,06 s | — |
| Corrección con la recta de la isla, giroscopio al 94 % | 75 % | 320/320, 37,06 s | — |
| **Código actual, giroscopio exacto** | 79 % (252/320) | 320/320, 36,90 s | 60/60, 41,92 s |

- **Las dos formas de ver el fin de la isla se quedan**: cada una sola pierde puntos o tiempo.
- **La corrección de rumbo es imprescindible en el coche** y ahora usa la recta de la isla que ya se ajusta para
  encontrar su fin. Salen `wall_heading()` (25 líneas), `island_end()` y dos constantes de `scene.py` (143 → 112
  líneas).
- La recta de la isla acepta ahora el coche hasta 30° torcido (antes 17°; `MAX_SLOPE`), el mismo alcance que tenía
  la corrección con dos rectas. Mismos resultados en las tres medidas.

## Corrección: con 9 salidas (12 nov 2026)

Las tres pasadas se midieron desde una sola salida (x = 0, y = −1,15). El entrenador preguntó por las salidas y la
medida con 9 por ronda (`open_lab --starts grid`: 3 a lo largo de la sección × 3 a lo ancho del pasillo, 16 islas × 2
sentidos × 3 semillas = 864 rondas, giroscopio al 94 %) encontró dos regresiones de la segunda pasada:

| Código | 9 salidas, sin huecos |
|---|---|
| Antes de la segunda pasada (`7d3ba88`) | 864/864 |
| Segunda y tercera pasada (`48cbe67`) | 730/864 (84,5 %) |
| … con el freno final esperando a que el coche esté recto | 841/864 (97,3 %) |
| … y la distancia con límite de aceleración en vez de la velocidad mandada | 852/864 (98,6 %) |
| **… y la odometría LiDAR de vuelta (código actual)** | **864/864** |

- **Freno final con las ruedas giradas (100 rondas).** Saliendo 30 cm detrás del centro de la sección, la última
  curva termina ya en el punto de parada. La misión frenaba al instante, con las ruedas a tope: una velocidad 0 deja
  las ruedas donde están (`base_adapter` hace lo mismo en el coche) y el coche rodaba hasta la isla. El arco a giro
  completo lo destapó; el arco anterior terminaba más recto. Ahora `_finish` no frena hasta estar a menos de
  `FINISH_STRAIGHT` (0,1 rad) de la recta.
- **Primera curva al instante (22 rondas).** Saliendo 30 cm delante del centro y junto a la pared exterior, la
  distancia contada con la velocidad mandada daba 25 cm recorridos cuando el coche llevaba 2 cm (retraso del motor),
  y giraba pegado a la isla. **La odometría LiDAR vuelve**: `mission.step` recibe otra vez la distancia medida. Quitar
  la odometría queda descartado.
- De la segunda pasada siguen el arco a giro completo, el rearme por distancia y las tres constantes; de la tercera,
  el rumbo con la recta de la isla.
- Con el código actual: 864/864 con el giroscopio exacto y al 94 %; con huecos de LiDAR (estrés) 76 %; modelo de
  Gazebo 60/60 a 41,92 s desde la salida estándar y 324/324 desde las 9 salidas.
- **Regla desde ahora:** un cambio del Open se mide con `--suite centres --starts grid`, no desde una sola salida.

## Sin odometría y parada en seco (12 nov 2026)

Dos preguntas del entrenador: «¿hay forma de quitar la odometría?» y «¿por qué no frenar a 0 de golpe?».
Medido con `--suite centres --starts grid` (9 salidas), giroscopio al 94 % salvo donde se indica.

**Odometría.** Solo servía para saber que el coche avanzó `ARM_DISTANCE` (25 cm) en la recta. Ahora esa distancia
es cuánto se acercó la pared de enfrente desde que empezó la recta (el `front_axis` del escaneo, una medida):

| Distancia recorrida | 9 salidas × 9 semillas |
|---|---|
| Odometría LiDAR | 2591/2592 |
| Velocidad mandada × tiempo (descartado) | 730/864 con 3 semillas |
| **Pared de enfrente (actual)** | 2590/2592 |

`mission.step(dt, scene, gyro_z, camera)` ya no recibe distancia; el nodo y el lab no usan `LidarOdometry`.

**Parada en seco.** `base_adapter` bajaba la velocidad a 0,6 m/s² (`decel_limit`): desde 0,64 m/s son ~34 cm rodando
con las ruedas donde estaban. En el coche, `car.launch.py` pone ahora `no_ramp_states` =
`FINISH,DONE,CRASH,OPERATOR_STOP` para el Open; en el lab, `stop_dead: true` en `real_car_v4.yaml`.

| Final de ronda | Buenas (9 salidas) | Válidas para el juez |
|---|---|---|
| Rampa, sin esperar a estar recto (el fallo) | 744/864 | 173/864 |
| Rampa, esperando a estar recto, `finish_lead` 0,25 | 2590/2592 | ~20 % (deriva de mm tras DONE) |
| En seco, `finish_lead` 0,25 | 792/864 (para 11 cm antes y queda fuera) | 791/864 |
| En seco, `finish_lead` 0,14, sin esperar a estar recto | 860/864 | 858/864 |
| **En seco, `finish_lead` 0,14, esperando (actual)** | **2576/2592 (99,4 %)** | **2575/2592** |
| … lo mismo con el giroscopio exacto | 864/864 | 864/864 |

- Con la parada en seco, esperar a estar recto ya no cambia el resultado; se queda (3 líneas) porque protege a
  cualquier coche con rampa, como el modelo de Gazebo.
- Lo que queda (16 de 2592): 2 roces con la isla en FINISH en pasillo estrecho, y paradas ~25 cm antes de tiempo
  saliendo desde atrás: recién salido de la última curva el rumbo creído va 4–8° mal (giroscopio al 94 %) y el rayo
  de frente roza el costado de la isla. Probado y descartado: corregir el rumbo sin esperar 25 cm tras la curva
  (97 %), y no frenar hasta que la pared de la isla diga «recto» (2585/2592, dentro del ruido y una regla más).
- Estrés con huecos de LiDAR: 75 %. Modelo de Gazebo: 60/60 a 41,92 s y 324/324 desde las 9 salidas.
- `finish_lead` 0,14 sale del lab: **hay que comprobarlo en el coche** (dónde para respecto a la salida).
