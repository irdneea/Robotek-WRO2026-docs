# Open v5: reimplementación desde cero con el mínimo de código y estados

> **Estado (21 oct 2026): es un plan de diseño, no hay código v5.** Lo que sí está hecho es la
> investigación del v4 que lo respalda: 27 rondas de ablación en Gazebo, 12 ablaciones sintéticas y el
> análisis de las 24 rondas del set estándar. Todo lo que dice «medido» sale de ahí y se puede repetir
> con los comandos de [Cómo repetir la investigación](#cómo-repetir-la-investigación).

## 1. Idea y regla del juego

El v4 se obtuvo tocando cosas durante meses y después se simplificó sin cambiar su comportamiento
(hallazgos). Eso dejó 8 estados, 49 parámetros y unas 560 líneas de
decisión más 100 de visión. El v5 hace la pregunta contraria: **¿qué es lo mínimo que resuelve el Open
en el coche real?** Se parte de lo que el coche necesita y se usa el v4 como **fuente de datos**, no como
plantilla: cada pieza del v4 solo entra al v5 si una prueba demuestra que sin ella la ronda falla o
empeora.

Reglas de partida (las mismas que el v4, [AGENTS.md](../AGENTS.md)):

- Solo LiDAR, giroscopio y cámara, con ruido; nada de pose real ni encoders.
- Dirección de las ruedas limitada a ±25° por regla y a 17,6° reales (`REAL_STEER_LIMIT`).
- Gana por puntos (30 máximos) y después por tiempo total desde Start.
- `robotek_open` solo depende de `robotek_common`.
- Código en inglés, prosa en español, un commit por cambio verificado.

## 2. Qué problema es realmente

Tres vueltas a un cuadrado alrededor de una isla, 12 esquinas, y parar en la sección de salida.
Sin obstáculos. Se reduce a cuatro preguntas:

| Pregunta | Cómo la responde el coche |
|---|---|
| ¿Hacia dónde voy? (el sentido es aleatorio) | las líneas azul y naranja del suelo, con la cámara |
| ¿Cómo voy recto? | giroscopio para el rumbo y LiDAR para la distancia a la pared |
| ¿Cuándo giro? | cuando la pared de enfrente está cerca **y** termina la isla |
| ¿Cuándo paro? | tras la esquina 12, cuando vuelve a ver la misma distancia frontal que vio al salir |

## 3. Lo que dicen los datos del v4

### 3.1 Qué se usa y qué no

De las 24 rondas del set estándar (`refac2-a`, `refac3-a`):

| Dato | Medido | Consecuencia |
|---|---|---|
| Estados que aparecen en la telemetría | `CALIBRATE`, `FOLLOW`, `TURN`, `FINISH`, `DONE`. **Nunca `RECOVER`.** | en el modelo del simulador no hay atascos; `RECOVER` solo se ha visto en 16 de 130 rondas de las series del coche real |
| Motivo de la dirección | 24 de 24 `camera_confirmed`; el veto del LiDAR (`direction_hint`) no intervino nunca | se puede quitar la pista del LiDAR sin cambiar el resultado |
| Qué dispara cada giro (144 giros) | **96** con isla terminada por el extremo detectado (`endpoint_ready`) y el lado aún cerrado; **35** solo con el lado abierto; **13** con ambos | el extremo de la isla es la señal que manda, no el lado abierto |
| `finish_distance` | vale 0 en v4 | la parada por distancia no se usa; solo la parada por distancia frontal |
| `front` y `wall_yaw` de la percepción | solo se graban en telemetría | no hacen falta para decidir |

### 3.2 Ablaciones en Gazebo

Cada fila quita **una** pieza del perfil v4 y corre tres rondas (`square100` CCW, `square180` CW,
`rect180x100` CCW), sin ventana a ×2. Referencia v4 (`refac3-a`): 30 puntos en 33,3 s, 50,9 s y 43,0 s.

| Ablación | Resultado | Veredicto |
|---|---|---|
| `heading_kd = 0` | 30 puntos, 33,5 / 50,9 / 43,1 s: **idéntico** | el amortiguamiento en recta no hace falta |
| `turn_rate_damping = 0` | 11 / 9 / 13 puntos, inválidas | **imprescindible** |
| `turn_exit_angle = 0` (sin aflojar al final del arco) | 15 / 11 / 12 puntos, inválidas | **imprescindible** |
| `corner_lookahead = 0` (sin señal del extremo de la isla) | 24 / 10 / 11 puntos, inválidas | **imprescindible** |
| `corner_endpoint_confirmations = 1` | 18 / 11 / 13 puntos, inválidas | **imprescindible**: un solo escaneo se confunde con ruido |
| una sola velocidad (sin `first_corner_speed`, `last_corner_speed` ni `last_corner_speed_scale`) | 4 / 18 / 10 puntos, inválidas | **imprescindible**: la última esquina más lenta es lo que deja parar dentro de la sección (cuál de los tres hace el trabajo no se separó) |
| `inner_lane_margin = 0` | 30 puntos, 33,3 / 51,5 / 42,5 s | sin efecto en carril ancho; en el estrecho (`square180`) el coche queda rozando la isla (margen «justo»): el margen hace falta como **separación mínima de la isla** |
| `turn_front_latency = 0` | 30 puntos, 34,1 / 51,0 / 43,7 s | se puede quitar: cuesta entre 0,1 y 0,8 s |
| `finish_brake_speed = 0` | 30 puntos, 33,3 / 51,0 / 43,1 s: **idéntico** | se puede quitar |

Las 27 rondas están en `docs/open-challenge-runs/*-v5abl-*`.

### 3.3 Qué no se puede sacar del oráculo sintético

El oráculo `golden_open.py` fue útil para refactorizar, pero **no sirve para decidir qué piezas hacen falta**:

- **No modela colisiones.** Con carriles de 0,6 m (isla de 1,8 m, el campo `square180`, que en Gazebo
  pasa) el coche sintético se sale por la pared y sigue de largo: `ccw_lane60` y `cw_lane60` terminan en
  `FOLLOW` con 1 giro. El golden graba un fallo del arnés, no una propiedad del robot.
- **Tiene actuadores perfectos.** Sin retraso de servo, quitar el amortiguamiento, el aflojado del
  arco o la señal del extremo **no rompe nada** (de 11 ablaciones solo una, quitar el sesgo lateral, falla y
  solo en un carril estrecho), mientras que en Gazebo con `real_car:=true` esas tres rompen la ronda.

Conclusión de método: las decisiones de «esto hace falta» se toman en Gazebo con el modelo de actuadores
del coche real; el oráculo sintético solo sirve para comprobar que un refactor no mueve decisiones.

### 3.4 Lo que ya sabemos que es esencial

1. **Un solo ciclo de rumbo.** En recta y en el arco el v4 usa dos leyes parecidas
   (`heading_kp·err − heading_kd·gyro` y `turn_heading_gain·err + feedforward − turn_rate_damping·(gyro − nominal)`);
   las dos constantes de amortiguamiento valen 0,1.
2. **Giro = rampa del rumbo de referencia** a la velocidad angular que da el volante al tope, aflojando
   el *feedforward* al final (`turn_exit_angle`).
3. **Disparo del giro** = pared de enfrente a menos de un umbral **y** extremo de la isla cerca
   (`corner_lookahead`), con 2 escaneos distintos que lo confirmen.
4. **Última esquina más lenta** y parada por distancia frontal igual a la del inicio.
5. **El coche va pegado a la isla**: `outer_lane_distance 0,8` con `inner_lane_margin 0,25` hace que, en
   un carril de 1 m, el objetivo sea quedar a ~0,25 m de la isla (el camino más corto), no al centro.

## 4. Diseño v5

### 4.1 Principios

- **Una ley de control**, no dos. El giro es el mismo lazo de rumbo con la referencia en rampa.
- **Una observación de 4 campos** (lo que de verdad usan las decisiones), en vez de 13.
- **Tres estados** y un motivo de parada.
- **Constantes del coche en `vehicle.py`**, no parámetros: límite de volante, distancia entre ejes, escala
  de velocidad medida.
- Parámetros solo para lo que se ajusta en la pista (≤ 12); el resto son constantes con nombre.
- El nodo ROS, la visión HSV y la telemetría **se conservan** tal cual (no son la lógica del Open y ya
  funcionan en el coche); lo nuevo es el núcleo `decisión + percepción del LiDAR`.

### 4.2 Contrato de datos

```python
@dataclass(frozen=True)
class Scene:                  # una por escaneo de LiDAR
    left: float               # mediana a ±90° (m), inf si falta
    right: float
    front_axis: float         # distancia a la pared de enfrente sobre el eje de la pista
    island_end: float         # x del extremo visible de la isla en el marco del coche, inf si no hay
```

`island_end` conserva la señal que el v4 llama `corner_distance`. La parte de la percepción que más pesa
en el v4 es justamente esa estimación (ajuste de recta y recorrido del último punto conectado, unas 55
líneas). En el v5 se prueba primero una versión mucho más corta (hipótesis H1 de §6) y solo si falla se
vuelve a la del v4.

Se **dejan fuera**: `front`, `wall_yaw`, `wall_valid`, `direction_hint`, `side_open` como campo
(se deriva de `left`/`right`).

### 4.3 Máquina de estados

| Estado | Qué hace | Sale cuando |
|---|---|---|
| `SETUP` | quieto: espera Start, calibra el giroscopio, toma la distancia frontal de salida y decide el sentido con la cámara | hay sentido → `RUN` |
| `RUN` | un solo lazo de rumbo. La fase (recta, arco o final) es **dato**, no estado: `turns` y `arc_until` | tras la esquina 12 y frenada en la distancia de salida → `STOP` |
| `STOP` | parado para siempre, con motivo `done`, `direction_fault` u `operator_stop` | — |

`STALLED` y `RECOVER` **no están** en el núcleo: en el modelo del simulador nunca ocurren (§3.1). Si las
pruebas con el coche real los piden, entran como un subestado de `RUN` con contador, no como estados nuevos.

### 4.4 Lógica de `RUN` (pseudocódigo)

```python
def step(dt, scene, imu):
    # 1) velocidad
    v = cruise if turns < 11 else last_corner_speed
    v = min(v, brake_to(scene.front_axis - trigger(v)))          # frena hacia el umbral de giro

    # 2) ¿empieza un giro?
    if armed and scene.front_axis <= trigger(v) and island_end_seen(scene):   # 2 escaneos seguidos
        yaw_goal += turn_dir * pi/2; turns += 1; armed = False; arc_t = 0

    # 3) rampa del rumbo de referencia y ley única
    rate = v * tan(STEER_LIMIT) / WHEELBASE * speed_scale
    yaw_ref = slew(yaw_ref, yaw_goal, rate * dt)
    err = yaw_goal - yaw
    ff = turn_dir * STEER_LIMIT * min(1, abs(err) / exit_angle) if yaw_ref != yaw_goal else 0
    steer = clamp(KP * (yaw_ref - yaw) + ff - DAMPING * (imu.rate - ref_rate) + lateral(scene), ±STEER_LIMIT)

    # 4) rearme y fin
    armed |= (yaw within tol of yaw_goal) and island_beside(scene) and travelled > arm_distance
    if turns == 12 and arrived_at_start(scene.front_axis): stop('done')
    return v, steer
```

`lateral(scene)` es la rueda hacia la isla: mantiene `inner_gap` (~0,25 m) y vale 0 mientras el lado interior
está abierto (en la esquina). Sustituye a `outer_lane_distance`, `inner_lane_margin`, `outer_lane_gain` y
`outer_lane_max` del v4.

### 4.5 Parámetros v5 (objetivo: 12 o menos)

| Parámetro | Valor inicial (del v4) | Por qué se mantiene |
|---|---|---|
| `cruise_speed` | 1,28 | tiempo de ronda |
| `last_corner_speed` | 0,6 | §3.2: imprescindible para parar dentro de la sección |
| `inner_gap` | 0,25 | reemplaza cuatro valores del carril |
| `turn_front_distance` | 1,04 | umbral de pared de enfrente |
| `corner_lookahead` | 0,35 | §3.2: imprescindible |
| `finish_speed` | 0,15 | aproximación final |
| `finish_lead` | 0,08 | frenada final |
| `finish_stop_wait` | 0,9 | asentamiento del motor |
| `calibrate_seconds` | 0,3 | calibración del giroscopio |
| `direction` | `auto` | `ccw`, `cw` o `auto` |
| `direction_confirmations` | 3 | cuadros seguidos de la cámara |
| `scan_max_age`, `imu_max_age` | 0,35 y 0,2 | frescura de sensores (nodo) |

Pasan a **constantes con nombre**: `KP 0,8`, `DAMPING 0,1` (un solo valor para recta y arco),
`exit_angle 0,25`, `endpoint_confirmations 2`, `arm_distance 0,25`, la tolerancia de giro, el tiempo
máximo de un arco, `STEER_LIMIT` y `speed_scale` (de `vehicle.py`).

**Se eliminan** (con su prueba de §3): `heading_kd`, `turn_front_latency`, `finish_brake_speed`,
`inner_lane_margin`, `outer_lane_*`, `finish_distance`, `first_corner_speed`, `turn_front_yaw_accel`,
`turn_front_carry_gain`, `brake_decel` (se vuelve una rampa lineal), `follow_gyro_gain`, `approach_distance`.

### 4.6 Tamaño objetivo

| Medida | v4 hoy | Meta v5 |
|---|---|---|
| Estados | 8 | 3 |
| Parámetros de ROS | 49 | ≤ 12 (más 3 de visión) — **cumplido en el laboratorio: 10** |
| Campos de la observación | 13 | 4 — **cumplido** |
| Líneas con código, decisión + percepción del LiDAR | 558 | ≤ 250 — **cumplido: 232** |
| Función más compleja | 11 (decisión) | ≤ 8 — **cumplido: 8** |

Se mide con el mismo contador de líneas y complejidad que en los
hallazgos para que sea comparable.

## 5. Plan de pruebas

El fallo que más se repite en este proyecto es validar con algo demasiado indulgente (§3.3). El plan es
por capas, y cada capa tiene que pasar antes de la siguiente:

| Capa | Qué | Cuándo falla |
|---|---|---|
| 1. Unitaria | `Scene` desde un escaneo armado a mano; `step` con escenas fijas: recta, esquina, fin | segundos; sin simulador |
| 2. Laboratorio (nuevo) | el arnés sintético **con colisiones y con el modelo de actuadores** de `sim_actuator_model.py` (retraso y velocidad del servo) y el límite real de 0,307 rad, y con los mismos campos que el set estándar | ~2 s; sirve para iterar rápido |
| 3. Gazebo sin ventana | set estándar de 12 rondas contra el v4 (`compare_open_suites.py refbase-a refbase-b vs v5-a`) | ~12 min |
| 4. Gazebo con ventana | `square100` CCW y CW, a ×1 | ~2 min |
| 5. Coche real | H-pruebas del [roadmap](roadmap-robot-nuevo.md) | pendiente: IMU y servo del montaje nuevo |

### Criterios de aceptación del v5

1. 12/12 rondas válidas, 30 puntos, margen «cómodo» o «justo» (igual que el v4).
2. Tiempo medio del set dentro de **+1,0 s** del v4 (`refac3-a`) y ninguna ronda fuera de la dispersión
   del v4 más 1,0 s.
3. Las metas de §4.6 (estados, parámetros, líneas).
4. Lo que el v4 hace y el v5 no (recuperación de atascos, veto del LiDAR) queda anotado como **límite**
   con la evidencia de que no se usó, no como mejora.

## 6. Hipótesis a probar (cada una con su experimento)

| # | Hipótesis | Cómo se prueba | Si falla |
|---|---|---|---|
| H1 | **Cumplida (21 oct)**: el extremo de la isla se halla con un salto de rango entre rayos contiguos (≈ 30 líneas) en vez de ajustar una recta | capa 2 (igualar el `corner_distance` del v4 en las 12 misiones); capa 3 siempre | volver al ajuste del v4 |
| H2 | **Cumplida en el laboratorio**: una sola ley de rumbo con referencia en rampa reemplaza al arco temporizado | falta capa 3 | recuperar el arco temporizado solo para el último giro |
| H3 | **Cumplida en el laboratorio**: `inner_gap` fijo reemplaza los cuatro valores del carril | falta capa 3 (`square180`) | mantener `inner_lane_margin` |
| H4 | La frenada hacia el umbral puede ser lineal en vez de `sqrt(2·a·gap)` | capa 3 con `brake0` como referencia de lo poco que pesa | volver a la raíz |
| H5 | `turn_front_latency = 0` y sin términos de aceleración del volante cuestan ≤ 1 s | §3.2 ya lo cumple para la latencia; faltan los términos fijos | dejar un único término de latencia |
| H6 | `SETUP` como un solo estado (calibrar + sentido) no cambia nada | capa 1 | separar `CALIBRATE` |
| H7 | **Sin LiDAR para el sentido**: la cámara decide sola (24/24 en el set) | ya medido, falta con el coche real y la cámara real | volver a la pista del LiDAR |
| H8 | La parada puede ser un único criterio: distancia frontal = distancia de salida + `finish_lead` | capa 3: la separación entre `finish_initial_front_lead` y `finish_settle_seconds` | recuperar el mezclado del v4 |

## 6 bis. Resultado del núcleo (21 oct 2026, solo laboratorio)

[`v5/mission.py`](../src/robotek_open/robotek_open/v5/mission.py) implementa `SETUP` → `RUN` → `STOP` con una sola ley de
rumbo, y [`open_lab.py`](../src/robotek_evaluation/robotek_evaluation/open_lab.py) lo corre con `--strategy v5`.
Primera ejecución del set estándar, sin ajustar nada después de escribirlo: **12/12 válidas con 30 puntos**.
Con 6 semillas por campo (72 rondas por estrategia, laboratorio):

| | v4 | v5 |
|---|---|---|
| Válidas | 72/72 | 72/72 |
| Tiempo medio (s) | 40,80 | 40,74 (diferencia pareada −0,06 s; entre −0,50 y +0,80) |
| Margen mínimo / medio al muro (m) | 0,075 / 0,122 | 0,082 / 0,122 |

Tamaño (mismo conteo que los hallazgos, sin visión ni nodo):

| Medida | v4 | v5 |
|---|---|---|
| Estados | 8 | 3 (`SETUP`, `RUN`, `STOP`) |
| Campos de la observación | 13 | 4 |
| Parámetros de ROS | 49 | 10 (`Params`) |
| Líneas con código (decisión + percepción del LiDAR) | 558 | 232 |
| Complejidad total / máxima por función | 184 / 11 | 87 / 8 |

**Hipótesis:** H2 (una ley de rumbo con referencia en rampa), H3 (`inner_gap` fijo), H5 (sin latencia ni términos de
aceleración del volante) y H6 (`SETUP` como un solo estado) **se cumplen en el laboratorio**. H4: la frenada es lineal
(`BRAKE_GAIN`) y solo actúa en la última esquina, porque en el v4 de hoy `cruise_speed = corner_speed` y la raíz
cuadrada no se usaba antes. H8: la parada usa un solo `finish_lead`, sin el mezclado del v4.

**Lo que el v5 todavía no hace y el v4 sí:** `RECOVER` y `STALLED` (sin recuperación de atascos); el avance lento mientras
espera la dirección; el veto del LiDAR sobre la cámara; la parada por distancia; el control de frescura de sensores
(es del nodo, que aún no existe para el v5). Los 11 puntos de arriba son **del laboratorio**, que pasa lo que Gazebo no
(ver [open-lab.md](open-lab.md)): el v5 no ha corrido en Gazebo ni hay nodo ROS para correrlo.

## 6 ter. Resultado en Gazebo (21 oct 2026)

Nodo ROS: [`v5/node.py`](../src/robotek_open/robotek_open/v5/node.py) (`open_strategy_v5`, nodo `open_strategy`, mismos
tópicos, reloj y archivos que el v4), perfil [`open_v5.yaml`](../src/robotek_open/config/open_v5.yaml). Se elige con
`strategy:=v5` en `open_challenge.launch.py` y con `--strategy v5` en `run_gui_experiment.sh`.

Set estándar de 12 rondas, sin ventana a ×2, `real_car:=true`, ganancia de dirección 20 (`std12-v5-e-*`):

| | v4 (`refac3-a`) | v5 |
|---|---|---|
| Rondas válidas con 30 puntos | 12/12 | **12/12** |
| Tiempo medio frente a las referencias del v4 | — | **+0,04 s** (mayor +0,39 s); 12/12 dentro de la dispersión |
| Margen mínimo / medio al muro | 0,096 / 0,119 m | 0,094 / 0,119 m |
| Clase de margen | «cómodo» en las 12 | «cómodo» en las 12 |

`compare_open_suites.py refbase-a refbase-b vs v5-e` y `refac3-a vs v5-e` dan «12/12 consistent with the reference spread».
Con ventana y a velocidad normal (`square100`, `v5-gui-sq100-*`, rondas limpias: sin atraso del nodo): **CCW** 30 puntos en
**33,197 s** simulados (33,6 s de pared) y **CW** 30 puntos en **32,897 s** (33,3 s), ambas válidas con margen «cómodo»
(0,141 y 0,136 m). Con el v4 y el mismo montaje: 33,397 s y 32,797 s.

### Lo que salió mal en el camino (y por qué importa)

Hubo **8 rondas del v5 inválidas que no son del v5**: las corridas `v5-a` (2 campos), `v5-b`, `v5-c` y `v5-d`, y 6 intentos de
`v5-e`. Tres causas, todas del banco de pruebas:

1. **El equipo estaba cargado** (un juego a ~300 % de CPU, carga media de 20 a 26): el nodo se atrasaba de 0,3 a 2 s respecto al
   simulador, y el coche recibía escaneos viejos. Se detecta porque el sello de los escaneos se adelanta al reloj `/clock`
   (+0,3 a +2 s) y los ticks del control se separan hasta 0,7 s.
2. **`clean_sim.sh` no mataba `open_strategy_v5`** (su patrón solo conocía `open_strategy`): al interrumpir un lote quedaron
   nodos del v5 vivos, publicando órdenes que se mezclaban con las de la ronda siguiente (la dirección giraba sola antes de
   arrancar). Corregido (`open_strategy(_v5)?`).
3. **Mi primer filtro de calidad solo miraba los primeros 13 s** de cada ronda y dejó pasar rondas con el atraso al final
   (`shift140` CCW falló en la parada por eso). Ahora mira toda la ronda: [`tools/open_suite_quiet.sh`](../tools/open_suite_quiet.sh)
   espera carga ≤ 8 y repite hasta 3 veces una ronda cuyo nodo se atrasó.

Las rondas contaminadas se conservan como intentos. Cada campo del set tiene al menos una ronda **limpia** (atraso < 0,1 s en
toda la ronda) y las 12 limpias son las del resultado.

**Un error mío que sí era del v5 y se corrigió:** la estimación del extremo de la isla con una distancia lateral constante
(tolerancia 6 cm) falla cuando el coche está inclinado 0,07 rad respecto a la pared, y giraba 0,3 m antes en `shift140`. Se
cambió por el ajuste de una recta a la pared (`v5/scene.py`) y se añadió una prueba con el coche inclinado.

## 7. Orden de trabajo

Cada paso es un commit con su prueba; no se mezcla con cambios del v4.

1. **Arnés de laboratorio** (capa 2): colisiones + actuadores del coche real. **Hecho el 21 oct 2026**
   ([open-lab.md](open-lab.md)): reproduce el set del v4 (12/12, 30 puntos, −0,65 s de media contra Gazebo; márgenes a ±2 cm en lo que pasa), pero
   **sigue sin reproducir las ablaciones que rompen Gazebo** (se corrigió el eje trasero y el servo; ver el límite en `open-lab.md`). Por eso solo sirve de filtro: lo que falla ahí falla; lo
   que pasa ahí aún hay que confirmarlo con Gazebo.
2. **Subpaquete `robotek_open/v5/`** (no un paquete ROS aparte: no hace falta otro `package.xml`; solo importa
   `robotek_common`) con `Scene` y la percepción mínima, más las pruebas de capa 1.
   **Hecho el 21 oct 2026**: [`v5/scene.py`](../src/robotek_open/robotek_open/v5/scene.py) (~70 líneas) y
   [`test_v5_scene.py`](../src/robotek_open/test/test_v5_scene.py) (16 pruebas). **H1 se cumple**: el extremo de la
   isla se halla con un salto de rango en lugar del ajuste de recta de unas 55 líneas, y en 12 rondas del laboratorio
   (7 683 escaneos en `FOLLOW`) coincide con el v4 a ≤ 5 cm en el 97,8 % de los escaneos; dentro de la
   anticipación de 0,35 m el v4 marca 1 498, el v5 1 499 y coinciden 1 489 (9 solo del v4, 10 solo del v5).
   `left`, `right` y `front_axis` son idénticos. Fuera de `FOLLOW` (en el arco) difieren y no se usan ahí. Se
   conserva `open_vision.py` y el nodo.
3. **Núcleo de `RUN`** con H2, H3, H4, H5. **Hecho el 21 oct 2026, solo en el laboratorio** (ver «Resultado del núcleo»); ronda a ronda en capa 2.
4. **Final** (H8) y `STOP`.
5. **Capa 3**: `tools/open_suite_quiet.sh <etiqueta>` y `compare_open_suites.py`. **Hecho (21 oct 2026)**: 12/12, +0,04 s.
6. **Capa 4** (ventana) y registro de las rondas.
7. Comparar con las metas de §4.6; informe corto con lo que cumple y lo que no.
8. Si pasa: perfil `open_v5.yaml` y selección por `profile:=` en `open_challenge.launch.py`; el v4 queda
   como el perfil de comparación hasta que el v5 pase el coche real.

## 8. Riesgos y cosas a decidir

- **El v4 funciona en el coche real parcialmente** (rondas `realcar-*`); el v5 no tiene todavía ninguna
  prueba real. El valor del v5 es sobre todo de **comprensión y de menor superficie**, no de velocidad:
  no se espera que sea más rápido que el v4.
- **Sin `RECOVER` no hay red de seguridad** contra un atasco real. Antes de quitarlo hay que decidir si el
  coche real lo necesita: 16 de 130 rondas del coche real entraron en `RECOVER`.
- **El modelo del simulador manda.** Si el modelo de actuadores no se parece al coche (servo y motor
  del montaje nuevo siguen sin medirse), las conclusiones de §3.2 pueden cambiar.
- Decidir si el v5 vive como paquete aparte o como perfil con el v4 dentro del mismo código: el segundo
  es más sencillo de mantener pero mezcla dos diseños; el primero respeta la regla de «no mezclar refactor
  con estrategia».

## Cómo repetir la investigación

```bash
# Las ablaciones del v4 (tools/open_param_ablation.sh, tools/open_ablation_synthetic.py) se borraron con el v4
# el 26 oct 2026; están en la historia de git (commit 2b17266 y anteriores).
# Qué disparó cada giro y qué estados aparecieron, a partir de la telemetría local de las rondas std12-*.
```

Las rondas de la tanda de ablación (`v5abl-*`) cuentan como intentos registrados y están en
`docs/open-challenge-runs/` con su `round.json`.
