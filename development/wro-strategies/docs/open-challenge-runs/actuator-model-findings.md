# Modelo de actuadores y reajuste del Open con servo rápido

Fecha: 6 de octubre de 2026. Branch: `extreme-testing`. Todas las rondas con GUI + RViz.

## 1. Hallazgo: el "retardo del servo" de la simulación era el plugin

- El plugin `AckermannSteering` de gz-sim 8 tiene un único `min/max_acceleration`
  (±2 en el URDF) que también limita los cambios de la velocidad de giro (yaw rate).
  La telemetría lo muestra: `gyro` y la rampa del controlador suben a 2 rad/s² y la
  rueda a ~16°/s (0,95 m/s), **igual con `steer_p_gain` 5 que con 20**.
- Por eso el retardo medido (0,35–0,52 s) no dependía de la ganancia del servo.
- Servo real estimado (HiWonder 15 kg·cm, 0,16–0,24 s/60°, rampa de la RRC Lite
  0,05–0,06 s): llega a 25° en ~0,1–0,15 s → equivale a ~15–30 rad/s² de yaw.

## 2. Modelo de actuadores (`sim_actuator_model`, opcional)

`actuator_model:=true` en `open_challenge.launch.py` / `obstacle_challenge.launch.py`:

- La estrategia publica `/cmd_vel_raw`; el nodo publica `/cmd_vel` al plugin.
- Dirección: retardo `steer_delay` 0,03 s, velocidad `steer_rate` 4,4 rad/s (~250°/s,
  servo a 5 V), primer orden `steer_tau` 0,03 s, límite ±25°.
- Motor: `accel_max` 2,0 m/s² (igual que antes, para cambiar solo el servo).
- El límite del plugin sube a 30 para que deje de mandar (`ackermann_acceleration`).
- Por defecto **apagado**: los resultados anteriores siguen siendo comparables.
- Verificado: la rueda llega a 25° en ~0,2 s (antes ~13° en 0,9 s).

Runners: `--launch-arg actuator_model:=true` (Open y Obstacle) queda en el manifiesto.

## 3. Iteraciones sobre la mejor ronda Open (`race-entry-v13`, shift140, CCW)

Un factor por vez. Columnas: modelo de actuadores, cambios respecto a v13, puntos
estimados, Start→DONE (s sim), giros, margen mínimo exterior/interior (cm), validada
(criterio interno: márgenes > 5 cm, 12 giros, parada en la sección de salida).

| Intento | Actuadores | Cambios | Pts | s sim | Giros | Ext/Int (cm) | Validada |
|---|---|---|---|---|---|---|---|
| `servo20-race-entry-v13-shift-ccw` | no (p=20.0) | — | 27 | 27.66 | 12 | 0.6/6.6 | no |
| `servo20-v13-latency05-shift-ccw` | no (p=20.0) | turn_front_latency=0.5 | 1 | 10.57 | 0 | 0.6/14.8 | no |
| `servo20-v13-latency03-shift-ccw` | no (p=20.0) | turn_front_latency=0.3 | 1 | 10.24 | 0 | 0.6/14.8 | no |
| `servo20-v13-outer020-shift-ccw` | no (p=20.0) | outer_lane_distance=0.2 | 27 | 27.55 | 12 | 0.6/6.1 | no |
| `actmodel-v13-shift-ccw` | sí | — | 0 | 9.57 | 1 | 28.7/-0.7 | no |
| `act-yawacc6` | sí | turn_front_yaw_accel=6 | None | — | None | —/— | no |
| `act-yawacc20` | sí | turn_front_yaw_accel=20 | None | — | None | —/— | no |
| `act-yawacc6b` | sí | turn_front_yaw_accel=6.0 | 0 | 9.50 | 1 | 28.5/-0.7 | no |
| `act-yawacc20b` | sí | turn_front_yaw_accel=20.0 | 0 | 9.50 | 1 | 28.6/-0.7 | no |
| `act-lat06` | sí | turn_front_latency=0.6, turn_front_yaw_accel=20.0 | 10 | 16.14 | 5 | 20.9/0.4 | no |
| `act-lat03` | sí | turn_front_latency=0.3, turn_front_yaw_accel=20.0 | 3 | 11.72 | 2 | 2.2/-0.7 | no |
| `act-lat00` | sí | turn_front_latency=0.0, turn_front_yaw_accel=20.0 | 7 | 16.66 | 3 | 0.6/14.8 | no |
| `act-lat06-steer035` | sí | turn_front_latency=0.6, turn_front_yaw_accel=20.0, turn_steer=0.35 | 10 | 16.89 | 5 | 26.8/-0.9 | no |
| `act-lat06-steer030` | sí | turn_front_latency=0.6, turn_front_yaw_accel=20.0, turn_steer=0.3 | 19 | 24.18 | 8 | 26.6/-5.1 | no |
| `act-lat06-steer025` | sí | turn_front_latency=0.6, turn_front_yaw_accel=20.0, turn_steer=0.25 | 25 | 24.24 | 12 | 18.3/-3.3 | no |
| `act-lat05-steer025` | sí | turn_front_latency=0.5, turn_front_yaw_accel=20.0, turn_steer=0.25 | 25 | 25.21 | 12 | 11.8/10.8 | no |
| `act-lat04-steer025` | sí | turn_front_latency=0.4, turn_front_yaw_accel=20.0, turn_steer=0.25 | 9 | 17.37 | 4 | 7.9/-0.7 | no |
| `act-lat05-steer025-fin06` | sí | turn_front_latency=0.5, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.6 | 30 | 26.20 | 12 | 10.9/8.2 | sí |
| `act-base-corner125` | sí | corner_speed=1.25, turn_front_latency=0.5, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.6 | 25 | 23.64 | 12 | 16.2/0.2 | no |
| `act-base-corner14` | sí | corner_speed=1.4, turn_front_latency=0.5, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.6 | 10 | 15.00 | 5 | 17.4/-1.2 | no |
| `act-corner125-lat045` | sí | corner_speed=1.25, turn_front_latency=0.45, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.7 | 30 | 24.95 | 12 | 11.8/8.0 | sí |
| `act-corner125-lat04` | sí | corner_speed=1.25, turn_front_latency=0.4, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.7 | 20 | 25.20 | 10 | 8.5/-0.7 | no |
| `act-c125-cruise18` | sí | corner_speed=1.25, cruise_speed=1.8, turn_front_latency=0.45, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.7 | 30 | 24.57 | 12 | 11.9/9.0 | sí |
| `act-c125-cruise22` | sí | corner_speed=1.25, cruise_speed=2.2, turn_front_latency=0.45, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.7 | 30 | 24.43 | 12 | 11.4/8.0 | sí |
| `act-c125-v18-brake19` | sí | brake_decel=1.9, corner_speed=1.25, cruise_speed=1.8, turn_front_latency=0.45, turn_front_yaw_accel=20.0, turn_steer=0.25, finish_distance=0.7 | 30 | 24.48 | 12 | 11.8/14.1 | sí |

Referencia (servo lento del plugin): `race-entry-v13-shift-ccw`, 30 pts, 26,04 s, 6,7/6,7 cm.

Hallazgos:

- Con el servo rápido el perfil v13 gira demasiado cerrado (toca la isla): estaba
  adelantando los giros para compensar ~0,5 s de un retardo que ya no existe.
- `turn_front_yaw_accel` (modelo del límite en el controlador) no cambió nada solo.
- Lo decisivo fue **girar más tarde** (`turn_front_latency` 1,0 → 0,45–0,5) y con
  **arco más abierto** (`turn_steer` 25° → 14,3°): la realimentación de rumbo completa
  el giro. Con 0,4 o menos vuelve a tocar.
- El tramo final (`finish_distance`) cambia: con giros más rápidos el coche termina el
  giro 12 antes y 0,3 m no alcanzan para entrar entero en la sección.
- Mejor ronda: 30 pts en **24,43 s** (vs 26,04 s con el servo lento). Crucero 1,8→2,2 o
  frenada 1,9 casi no cambian: el límite pasa a ser la entrada a las curvas.

> Los perfiles `open_strategy_actmodel_vN` se renombraron a `open_fastservo_vN`; las carpetas de
> rondas conservan su nombre original (`…-actmodel-vN-…`). Índice general: [perfiles.md](../perfiles.md).

## 4. Validación en 4 campos × 2 sentidos (GUI, salida y = −1,15)

| Perfil | Campo | Pts est. | s sim | Giros | Ext/Int (cm) | Recup. | Para en sección | Vueltas (GT) | Validada |
|---|---|---|---|---|---|---|---|---|---|
| `open_fastservo_v1` | shift140 CCW | 3 | 10.93 | 2 | 9.3/-1.3 | 3 | no | 0.398 | no |
| `open_fastservo_v1` | shift140 CW | 27 | 24.60 | 12 | 13.4/9.1 | 0 | no | 3.047 | no |
| `open_fastservo_v1` | square100 CCW | 22 | 26.78 | 11 | 13.0/-0.7 | 3 | no | 2.542 | no |
| `open_fastservo_v1` | square100 CW | 30 | 23.82 | 12 | 15.1/39.3 | 0 | sí | 2.992 | sí |
| `open_fastservo_v1` | square180 CCW | 30 | 24.79 | 12 | 8.4/8.3 | 0 | sí | 2.980 | sí |
| `open_fastservo_v1` | square180 CW | 30 | 24.50 | 12 | 11.3/6.6 | 0 | sí | 2.994 | sí |
| `open_fastservo_v1` | rect100x180 CCW | 30 | 24.23 | 12 | 12.2/14.8 | 0 | sí | 2.995 | sí |
| `open_fastservo_v1` | rect100x180 CW | 30 | 23.90 | 12 | 12.6/13.3 | 0 | sí | 2.989 | sí |
| `open_fastservo_v2` | shift140 CCW | 25 | 23.43 | 12 | 15.9/4.4 | 0 | sí | 2.985 | no |
| `open_fastservo_v2` | shift140 CW | 25 | 22.92 | 12 | 17.6/0.5 | 0 | sí | 2.981 | no |
| `open_fastservo_v2` | square100 CCW | 30 | 22.77 | 12 | 19.3/43.9 | 0 | sí | 2.978 | sí |
| `open_fastservo_v2` | square100 CW | 30 | 22.90 | 12 | 14.0/38.4 | 0 | sí | 2.987 | sí |
| `open_fastservo_v2` | square180 CCW | 25 | 23.80 | 12 | 11.9/3.3 | 0 | sí | 2.989 | no |
| `open_fastservo_v2` | square180 CW | 25 | 23.53 | 12 | 12.7/4.8 | 0 | sí | 2.974 | no |
| `open_fastservo_v2` | rect100x180 CCW | 30 | 23.02 | 12 | 17.8/8.4 | 0 | sí | 2.973 | sí |
| `open_fastservo_v2` | rect100x180 CW | 30 | 22.85 | 12 | 16.9/5.8 | 0 | sí | 2.980 | sí |
| `open_fastservo_v3` | shift140 CCW | 27 | 23.05 | 12 | 17.4/-1.7 | 0 | sí | 3.046 | no |
| `open_fastservo_v3` | shift140 CW | 27 | 22.96 | 12 | 20.2/-2.6 | 0 | sí | 3.053 | no |
| `open_fastservo_v3` | square100 CCW | 30 | 22.67 | 12 | 22.2/41.0 | 0 | sí | 3.036 | sí |
| `open_fastservo_v3` | square100 CW | 30 | 22.66 | 12 | 22.1/38.4 | 0 | sí | 3.039 | sí |
| `open_fastservo_v3` | square180 CCW | 10 | 16.49 | 4 | 19.6/-4.3 | 2 | no | 1.147 | no |
| `open_fastservo_v3` | square180 CW | 4 | 12.39 | 3 | 16.7/-0.7 | 3 | no | 0.617 | no |
| `open_fastservo_v3` | rect100x180 CCW | 27 | 22.92 | 12 | 21.2/-1.8 | 0 | sí | 3.043 | no |
| `open_fastservo_v3` | rect100x180 CW | 27 | 23.03 | 12 | 18.3/4.8 | 0 | sí | 3.034 | no |

| Perfil | Cambio | Válidas (criterio interno) | Completas 12 giros sin recuperación |
|---|---|---|---|
| `open_fastservo_v1.yaml` | v13 + latencia 0,45, `turn_steer` 0,25, curva 1,25, crucero 1,8, final 0,7 | 5/8 | 6/8 |
| `open_fastservo_v2.yaml` | v1 con latencia 0,50 y final 0,60 | **4/8** | **8/8**, 22,8–23,8 s |
| `open_fastservo_v3.yaml` | v2 con latencia 0,55 y final 0,65 | 2/8 | 6/8 |

Hallazgos:

- **`open_fastservo_v2` es el mejor**: las 8 rondas completan 3 vueltas sin recuperaciones y
  paran dentro de la sección de salida, en 22,8–23,8 s (vs 23,9–26,0 s del servo lento).
  Las 4 "no validadas" fallan **solo** por el margen a la isla < 5 cm (criterio interno):
  shift140 CCW 4,4 cm, shift140 CW 0,5 cm, square180 CCW 3,3 cm, square180 CW 4,8 cm.
  Sus 25 puntos vienen del estimador (`open_round_report.py:55`): si la ronda no es
  válida usa solo el progreso angular entero (2,98 vueltas → 2 vueltas, 23 secciones,
  sin parada). Las válidas tienen las mismas vueltas GT (2,97–2,99) y reciben 30.
  *Corrección: una versión anterior de este texto atribuía los 25 puntos a parar antes
  del punto de salida; era incorrecto.* Por reglamento la isla puede tocarse si no se
  mueve, así que probablemente valdrían 30, pero 0,5 cm es demasiado justo para el robot real.
- **La latencia de giro no es monótona**: 0,45 y 0,55 rozan la isla más que 0,50. En
  corredores de 0,6 m (square180) girar más tarde produce contactos y recuperaciones.
- `finish_distance`: 0,6 para antes del punto de salida (estimador), 0,7 se sale de la
  sección en CW en shift140; 0,65 llega pasado el punto de salida en todos los casos.
- Los parámetros dependen del modelo de servo **estimado**. Antes de seguir afinando hay
  que medir el servo real (retardo, velocidad, τ) y fijar esos valores en
  `sim_actuator_model`.

Reproducción:

```bash
bash src/robotek_evaluation/tools/run_gui_experiment.sh nombre \
  --params-file src/robotek_open/config/archive/open_fastservo_v2.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square180.sdf --direction ccw \
  --controller-direction auto --spawn-y -1.15 --rviz --ackermann-velocity-limit 4.0 \
  --ackermann-steer-p-gain 20 --launch-arg actuator_model:=true
```
