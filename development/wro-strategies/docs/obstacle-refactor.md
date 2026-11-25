# Obstacle: simplificación y refactorización

7 de octubre de 2026. Mismo método que el Open (open-refactor.md):
quitar lo que no corre, ordenar lo que queda y comprobar que el comportamiento es
idéntico. Referencia: commit `05a0eb3` (v8 honesto con replanificación síncrona).
Perfil nuevo: **`obstacle_sensors_v1`**, mismos valores de control que `obstacle_planner_v8`.

## Cómo funciona

```
LiDAR, giroscopio, cámara ─► obstacle_strategy_node
   rumbo = giroscopio integrado; distancia = odometría LiDAR (sin encoder)
        └─► ObstacleMission: CALIBRATE ─► DETECT_DIRECTION ─► ObstacleDriver
              CALIBRATE: quieto, promedia el giroscopio (sesgo)
              DETECT_DIRECTION: ajuste de muros CCW vs CW con el LiDAR; respaldo: líneas de cámara
              ObstacleDriver (PLAN … FINISH … DONE), en el marco de pista (siempre CCW, espejado en CW):
                 Localizer   — encaja el LiDAR contra los muros conocidos
                 SeatMap     — 24 asientos; LiDAR dice "hay algo", la cámara vota el color
                 BeamPlanner — secuencias de volante (modelo de bicicleta) sin tocar muros/pilares,
                               lado correcto de cada pilar; la que más avanza
                 seguimiento — pure pursuit, velocidad por curvatura y frenado; retroceso si no hay camino
```

## Qué cambió

- **Se quitó el controlador reactivo**, que no corría con el planificador: estados
  FOLLOW/TURN/ALIGN_EXIT/RECOVER/FINISH, lazo de carril, detección de esquinas, memoria de
  pilares, `steer_to_lane` y el modo de prueba en una recta del nodo (`full_round: false`).
- **Configuración**: `ObstacleConfig` con 43 campos usados (antes 102; desde el 7 oct, 9 parámetros + 33 valores fijos); los valores de v8 son
  los defaults. `obstacle_sensors_v1.yaml` solo trae `direction: auto`. Un parámetro retirado
  (p. ej. `cruise_speed`) se rechaza con un error que apunta al perfil nuevo.
- **`obstacle_planner.py` (600 líneas) partido** en `obstacle_field.py` (geometría de pista,
  coche, asientos), `obstacle_localizer.py`, `obstacle_seat_map.py`,
  `obstacle_beam_planner.py` y `obstacle_driver.py` (`ObstacleDriver`, antes `PlannerNavigation`).
- **Un solo flujo de movimiento**: el nodo entrega la distancia recorrida y el rumbo; ya no
  arma una posición `odom` que el planificador volvía a convertir en distancia. El sesgo del
  giroscopio vive en la misión (antes se leía de un controlador que no se usaba).
- **Constantes con nombre y una sola fuente**: distancia entre ejes, posición del LiDAR
  (0,06 m) y de la cámara (0,07 m, inclinación 0,4 rad, campo 60°), del URDF.
- **Replanificación síncrona** cada `plan_period` de reloj simulado (antes en un hilo, no
  reproducible). La opción de replanificar en un hilo (`plan_thread`) se retiró el 7 de octubre.
- **Grabación** separada en `obstacle_recording.py`, más `trace.jsonl.gz`: todas las entradas
  (IMU, scans, observaciones de cámara) y las órdenes de cada ciclo, para reproducir rondas.
- **Telemetría**: columnas de pose propia `x_track, y_track, th_track` (marco de pista) y
  `progress`; se retiran las del controlador reactivo (`target_y`, `turns`, `yaw_ref`…).
- **Runner**: preparación en `obstacle_experiment_setup.py`; el runner solo ejecuta, vigila y
  resume. Se retiró `--scope component` (un pilar en una recta) y las distribuciones
  `mixed/red/green`: solo la reglamentaria. Perfil por defecto `obstacle_sensors_v1.yaml`.
- Perfiles `obstacle_planner_v1–v11`, `obstacle_round_v1` y `obstacle_strategy`: retirados el 9 oct 2026 (usaban la pose de Gazebo); cada ronda grabada conserva su copia en `source/profile.yaml`
  (y en el historial de git, código de `05a0eb3`).

Código de estrategia: 1.911 → 1.319 líneas en 10 módulos de una responsabilidad; runner
299 → 254 (124 + preparación 130).

## Dónde modificar cada comportamiento

Módulos en `src/robotek_obstacle/robotek_obstacle/` (medidas del coche en `src/robotek_common/robotek_common/vehicle.py`; preparación de rondas en `robotek_evaluation`).

| Cambio deseado | Lugar |
|---|---|
| Velocidades, márgenes, costes, horizonte | `obstacle_config.py` (defaults) o el YAML |
| Calibración y elección de sentido | `ObstacleMission._step_calibrate()` / `_step_detect()` |
| Geometría de pista, asientos, medidas del coche y sensores | `obstacle_field.py` |
| Localización contra muros | `Localizer.correct()` |
| Pilares: detección y color | `SeatMap.lidar()` / `camera()` / `pillars()`; `obstacle_perception.py` |
| Reglas de la búsqueda (lado, radio, márgenes) | `BeamPlanner.plan()`, `BeamPlanner.wrong_side()` |
| Seguimiento, velocidad, final | `ObstacleDriver.step()` |
| Retroceso cuando no hay camino | `ObstacleDriver._choose_reverse()` / `_reverse_clear()` |
| Archivos de evidencia | `ObstacleRecording` |
| Mundo, pilares, sensores de auditoría, comando | `obstacle_experiment_setup.py` |

## Verificación

- **Equivalencia** (`tools/check_obstacle_refactor_equivalence.py`): reproduce cada traza con
  el código de `05a0eb3` (extraído de git) y con el nuevo, sin ROS.
  1. La reproducción de referencia replica exactamente las órdenes grabadas en la ronda real
     (valida el arnés).
  2. El código nuevo coincide con la referencia en **todos los ciclos**.
  
  Resultado: **6 rondas, 29.304 ciclos**, estados idénticos y órdenes iguales hasta el
  redondeo (máx. 9,5·10⁻¹⁵), incluidos PLAN_BLOCKED y PLAN_RECOVER
  ([detalle](obstacle-challenge-runs/obstacle-refactor-equivalence.json)).
  Rondas `ref-sync-reg0..2-*` (servo rápido, honesto, sin GUI), todas con 40 pts estimados.
- Limitación: en esas rondas el LiDAR decidió el sentido, así que el respaldo por cámara y el
  fallo de sentido no se ejercitan en la reproducción; los cubre una prueba unitaria.
- Pruebas: `test/test_obstacle_perception.py` (percepción, regla de lado, rechazo de
  parámetros retirados, calibración y sentido por cámara).
- Rondas reales con el código nuevo: ver [simulacion-honesta.md](simulacion-honesta.md).
