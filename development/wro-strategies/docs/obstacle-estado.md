# Obstacle: estado actual

Página corta para retomar el trabajo. **Se reescribe, no se le añaden secciones.** La historia, las
tablas y los hallazgos anteriores están en los documentos enlazados al final.

Actualizado: 8 nov 2026 (perfil del coche real `real_v3`; aparcamiento fijo `park_mode: 1`).

## Estrategia

- **v3 (por defecto desde el 3 nov 2026)**: `src/robotek_obstacle/robotek_obstacle/v3/`, perfil `config/obstacle_v3.yaml`, `--strategy v3`. Es
  el v2 con las esquinas puntuadas por el recorrido simulado, incluido el pilar del asiento contiguo, y con
  líneas buscadas por A\* para las esquinas S. Todo va en una tabla precalculada
  (`tools/build_corner_table.py`). Además: 0,15 m/s en las esquinas planificadas con < 7 cm, el tope de
  frente solo a < 0,55 m y los pilares de color desconocido abordados por el centro. Informe y decisiones: [obstacle-v3.md](obstacle-v3.md).
- **v2**: `src/robotek_obstacle/robotek_obstacle/v2/`, perfil `config/obstacle_v2.yaml`, `--strategy v2`.
- **Por defecto en todo:** el runner, el lab, `obstacle_lab_suite.py`, `obstacle_gazebo_batch.py`,
  `obstacle_challenge.launch.py` y el coche real (`robot.launch.py challenge:=obstacle`). En el coche, `mode:=`
  (vacío) da vueltas y aparca, `mode:=laps` solo da vueltas y `mode:=park` solo aparca; `strategy:=v2|v1` lanza los
  anteriores. El nodo original sigue con `--strategy current`
  (perfil `obstacle_sensors_v1.yaml`); un perfil que no es del v3 sin `--strategy` da error.
- **En el coche real** corre el port de robotek-learn (`robotek_obstacle_v3`), no `robot.launch.py`. Por defecto
  (robotek-learn `ffd8381`) se lanza `car.launch.py strategy:=robotek_obstacle_v3 camera_driver:=picam`, con:
  - 4 rps de tope;
  - `config/car_picam.yaml`: la cámara IMX708 y `steer_limit` 0,3054 (17,5°);
  - 20 s con `button:=false`.

  **12 nov 01:22 (1:1): sale del lote, 3 vueltas y aparcamiento parcial, DONE a los 105,9 s** (vueltas 34,3 / 26,8 /
  25,1 s, 19/19 señales `OK`); a las 02:39, en la prueba de solo aparcar (CCW), el parcial más los pulsos del
  entrenador lo dejaron en paralelo. En CW el aparcamiento aún no sale (posición 20–30 cm mal a lo largo de la recta;
  `park_fixed_sense:=2` sin probar en el coche). Detalle, comandos y pendientes:
  [hasta dónde llegó](robot-real-pi/obstacle-runs/20261111/README.md).
  **12 nov 00:02 (1:1): ronda completa, DONE a los 107,1 s** del Start (vueltas 36,2 / 33,1 / 33,8 s), sin
  aparcamiento ni salida del lote, sin juez.
  **11 nov 23:56 y 23:59 (1:1, `motor_rps_per_mps:=8.0`):** dos choques en la curva 6 porque la dirección no siguió a
  la orden (todo el giro mandado, el giroscopio casi en 0); vuelta 1 en 35,8–37,6 s
  ([notas](robot-real-pi/obstacle-runs/20261111/README.md)). El lab con `--car real_v4`: 195/200 sin aparcamiento.

  Mejor ronda: **DONE a los 85,0 s** del Start, sin aparcamiento ni juez (8 nov 2026, 23:08;
  [notas](robot-real-pi/obstacle-runs/20261108/README.md)). El aparcamiento en el coche todavía no sale.
- **Mapa del código:** `python3 tools/code_map.py src/robotek_obstacle/robotek_obstacle/v3/*.py`.

## Números de referencia

Coche de `2b17266` (el más reciente). El modelo de cada ronda se comprueba con `source_sha256` de su
`manifest.json`. En la competición siempre hay aparcamiento: se decide con el set **con** aparcamiento.

| Prueba | v2 | v3 (`7a02bae`) |
|---|---|---|
| Gazebo, set estándar con aparcamiento (layouts 0–4 × 2) | 5/10, 34,8 pts | **7/10, 46,5 pts** (`v3s-gz`) |
| Gazebo, campos S en CW (6 campos) | — | **6/6** (`v3s-gz-x`) |
| Lab con aparcamiento, layouts 0–49 × 2 × semillas 0–1 / 2–3 | 145 / 149 de 200 | **162 / 154 de 200, 49,5 / 48,8 pts** |
| Lab sin aparcamiento, layouts 0–49 × 2 × semillas 0–2 | 265/300 | **291/300** |

## Problemas abiertos, por valor

1. **Tiempo.** ~144 s con aparcamiento frente a 49–63 s del top 3 de 2025; en Gazebo `reg3-cw` se queda sin
   tiempo y `reg1-cw` llega a 176 s. El tope «algo a menos de 0,55 m → 0,2 m/s» domina, y a 0,30 m/s en
   curva el seguidor no aguanta. Aparcar a más de 0,06 m/s falla.
2. **Fallos de vuelta que quedan** (28 de 200 en el lab): `reg2-ccw` (también en Gazebo, contacto a 29 s),
   `reg16`/`reg17`/`reg27-cw` en el lab (pasan en Gazebo) y colores tardíos (`reg49-cw`).
3. **Aparcamiento:** `reg4-cw` en Gazebo termina las vueltas y no puntúa el aparcamiento.
   - Con el coche real (`real_v3`), el planificador aparca bien solo en 8 de 200 rondas del lab.
   - **El aparcamiento fijo (`park_mode: 1`, 8 nov) da 145/200 aparcados y 138/200 rondas válidas**
     ([obstacle-aparcamiento-fijo.md](obstacle-aparcamiento-fijo.md)).
   - Es sensible al lote: 1 cm de error cuesta 10–65 de 200, y el lote del campo aún no está medido.
   - **9 nov:** el coche real mide 24,5 cm, así que el lote de la simulación pasa a 1,5 × 0,245 = 0,3675 m
     (`vehicle.RULES_LENGTH`; antes 0,3495 m = 1,5 × 0,233 m del STEP). Los planificadores siguen con el contorno del STEP.
     Los demás números de aparcamiento de esta página son del lote de 0,3495 m.
   - **Lote de 0,3675 m (10 nov, `real_v3`, solo aparcar, capas 0–49 × 2 × semillas 0–1):** el fijo pasa de 195 a
     **197/200**, y el planificador de **35 a 173/200** (27 tocan un límite). Con el lote medido, el planificador
     vuelve a ser una opción: falta repetirlo con rondas completas y en el campo del coche.
   - Necesita ir despacio de verdad: con el piso de 0,25 m/s de `motor_min_rps` no aparca. Aún no se ha probado en el coche.

## Coche real en el lab (`--car real_v3`, 8 nov 2026)

Desde el 8 nov el motor del coche va en M2 **sin tipo de motor**: la placa controla la velocidad, un 0 normal lo para
y no hay resets. El perfil `real_v3` (`src/robotek_evaluation/config/real_car_v3.yaml`) es ese coche; `real_v2` queda
para reproducir las rondas del 1–4 nov (motor embalado, freno por reset). Medidas:
[robot-real-pi/obstacle-runs/20261108/](robot-real-pi/obstacle-runs/20261108/README.md); ajustes en su `lab-fit/`.

**Qué modela y con qué evidencia:**
- **Motor:** 4,4 rps por m/s; la velocidad real sigue a la pedida (0,045 / 0,09 / 0,16 / 0,28 / 0,45 m/s con 0,05 /
  0,10 / 0,165 / 0,33 / 0,55 pedidos). Respuesta de la placa: 0,10 s de tiempo muerto, 0,30 s de retraso y 1,0 m/s²
  (error medio 3,5 cm sobre 16 pulsos del 8 nov), más la rampa de `base_adapter` (1,0 / 0,6 m/s², también hasta 0).
  Tras un 0 desde 0,2 m/s rueda ~8 cm, como el coche.
- **Dirección:** el servo se satura en 1793 µs (0,307 rad, el `steer_limit` del v3). El coche gira 1,114 veces más que
  ese ángulo, con subviraje 0,10 s²/m²: radio de 0,335 m a 0,2–0,3 m/s y 2,28 rad/s a 0,8 m/s (pico de las rondas del
  Open del 8 nov). Tiempos del servo reajustados a las pruebas 11/13 y al cambio de lado de la ronda 2 del 4 nov
  (paso por cero del giroscopio a 1,658 s; real 1,66 s). La evidencia del radio va de 0,26 a 0,375 m:
  `--car-param steer_gain=1.0` (0,375 m) es el otro extremo.
- **Fallo opcional «todo el giro y no gira»** (pruebas 19/27 del 4 nov, ronda 3 del Open del 8 nov):
  `--car-param no_turn_lock=N` (N-ésima vez a tope, `no_turn_s` 2 s). Apagado por defecto.
- **Reproducción:** Open en el campo clásico 2/2, 12 giros, 23,5 s (real 26,7 s; el lab recorre menos camino). Ronda 2
  del 4 nov con su velocidad de entonces: rumbo máximo 55° a ~1,6 s, como el coche (54° a 1,6 s); el lab pasa con 4,3 cm
  y el coche tocó la isla.

**v3 en el lab, capas 0–49 × 2 sentidos** (sin aparcamiento salvo donde se dice):

| Prueba | Coche Gazebo | `real_v3` |
|---|---|---|
| Semillas 0–1 | 194/200, 109,1 s | **192/200, 124,1 s** (`steer_gain=1.0`: 196) |
| Semillas 2–3 | 194/200 | 195/200 |
| Con aparcamiento, semillas 0–1 | 156/200 | **8/200**; `park_mode=1`: **138/200** (145 aparcados) |
| `start_ramp=0.5`, semillas 0–1 / 2–3 | 194 / 194 | **194** / 195 (arregla `reg1-ccw`, el pilar de la recta de salida) |
| `start_ramp=0.5`, con aparcamiento | 154 | 7 |
| `approach_max` 0,35 / 0,5 / 0,7 rad | 177 / 194 / 192 | 177 / 191 / 192 |
| Planificador con `park_replan=1 park_approach_speed=0.25`, con aparcamiento, semillas 0–1 / 2–3 | 131 / 126 (de 156 / 161) | **102 / 107** (de 8 / 7) |
| Lo mismo + `known_speed_gain=1.5`, con aparcamiento | 127 / 133 | **120 / 117** |
| Esas dos opciones sin aparcamiento, semillas 0–1 / 2–3 | 194 / 194; con `known_speed_gain`, 188 / 190 | 192 / 195; con `known_speed_gain`, 190 / 194 |

- **Las vueltas van bien en el coche nuevo:** 192–195/200, ~15 s más lentas que en el coche de Gazebo (el motor
  tarda en acelerar y la velocidad real es ~0,9 de la pedida).
- **El aparcamiento no:** 132 de 200 rondas terminan «aparcado en parte o no paralelo», también con 300 s. Causa
  (capas 0–49, semilla 0, 100 rondas): el retraso del motor (sin él, 68/100) y el giro más cerrado (`steer_gain=1.0`,
  38/100). `park_speed` 0,04 da 13/100 (y baja el coche de Gazebo a 46/100); 0,10, 0/100. En vez de adaptar `park.py`,
  se hizo el aparcamiento fijo `park_mode: 1` (`v3/park_fixed.py`): solo aparcar, 195/200 frente a 35; ronda completa,
  145 frente a 10 ([obstacle-aparcamiento-fijo.md](obstacle-aparcamiento-fijo.md)).
- **Planificador adaptado (`park_replan`, `park_approach_speed`, 8 nov; apagados por defecto):** `park_replan=1`
  rehace el plan (A* desde la pose del coche, con tope de nodos para que sea determinista) cuando un movimiento termina
  a más de 2 cm / 6° de lo previsto o el plan acaba torcido más de 10°; además alarga la guarda con el rodaje.
  `park_approach_speed=0.25` va hacia el lote a 0,25 m/s mientras falta más de 0,30 m y retrocede a 2× `park_speed`
  lejos del final. En `real_v3` pasa de 8 a 102–107/200 (120 con `known_speed_gain=1.5`), pero en el coche de Gazebo
  baja de 156–161 a 126–133. **Quedan apagados**: no mejoran los dos coches, y el aparcamiento fijo da más en
  `real_v3` (138/200). Esperar a que la placa deje de rodar antes de replanificar dio más rondas sin tiempo y se quitó.
- **El salto de 0,30 m a la salida** (ronda 2 del 4 nov): `start_ramp` (unidades de pista; 0 = apagado) empieza la
  línea en el desvío real del coche y lo lleva al del primer pilar antes de su zona de mantenimiento (nunca rampas de
  menos de 0,3 unidades). En el campo de la ronda 2 baja el rumbo máximo de 48° a 23° con el motor nuevo. En el lab
  solo cambia `reg1-ccw` (+2) en `real_v3`; con aparcamiento −1 y −2. **Queda apagado** (no mejora los dos coches).
  `approach_max` (limitar el rumbo de aproximación a la línea) no mejora nada y se quitó.
- El coche viejo (`real_v2`) da 101/200: la v3 no funciona con el motor embalado, como en el coche.

## Cómo medir

```bash
tools/remote.sh sync                                                         # copia y compila en la remota
tools/remote.sh run python3 tools/obstacle_lab_suite.py --strategy v3 --layouts 0-49 --parking --seeds 0-1 --brief --out /tmp/x.json --against /tmp/base.json
tools/remote.sh run python3 tools/obstacle_gazebo_batch.py <tag> --strategy v3 --jobs 2 --rtf 1 --gpu --runner-arg=--layout=regulation-park
tools/remote.sh fetch && python3 tools/round_digest.py <ronda> [--at fault]
tools/remote.sh run python3 tools/build_corner_table.py                      # tras cambiar v3/corner.py; traer el archivo al Mac
```

- **Decidir con aparcamiento** (layouts 0–49 × 2 × 2 semillas, 200 rondas en ~2 min) y confirmar con otras
  semillas: con 1 semilla y 10 campos los cambios parecían mejoras y eran ruido.
- **Lab:** determinista. Un resultado distinto significa que cambió el código o el coche.
- **Gazebo:** como mucho 2 rondas a la vez, y **nunca con el lab corriendo** en la misma máquina (rompe la
  puerta de calidad). No usar `--rtf 0` para resultados.
- **No leer** `round.json`, la telemetría ni `planner.jsonl` enteros: usar `round_digest.py`.

## Historia y detalle

- [obstacle-v3.md](obstacle-v3.md): las ideas del top 3 de WRO FE 2025, cada hipótesis con su resultado, y
  por qué el v3 es c4.
- [obstacle-v2-next-steps.md](obstacle-v2-next-steps.md): iteraciones del 25–26 oct, capacidad de Gazebo
  y experimentos revertidos.
- [obstacle-reimpl-v2.md](obstacle-reimpl-v2.md): línea base, laboratorio, diseño del v2 y fases.
- [obstacle-reimpl-plan.md](obstacle-reimpl-plan.md): el plan y las decisiones del usuario.
- [maquina-remota.md](maquina-remota.md): la máquina remota y sus herramientas.
