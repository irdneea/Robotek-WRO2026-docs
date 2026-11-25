# Open real_car: comparación de robustez

Mismo modelo físico y juez; dirección equivalente ±17,6°, motor limitado a
100 % PWM (máximo 0,60 m/s inferido), control solo con sensores ruidosos.
El set estándar contiene seis geometrías en ambos sentidos. Un set parcial
se identifica como tal; una ronda exitosa no demuestra repetibilidad.
Primero puntos, después tiempo desde Start; la validación exige también
parada, ausencia de contactos y margen. No promover un perfil por tiempo
si pierde puntos o falla la validación. Las poses de auditoría no se entregan
al controlador.

[Historial, diagnósticos y GUI](realcar-starts-history.md).
[Mejores por contexto y motivos](realcar-robust-best-rounds.md).
[Guía de ejecución](../guia-correr-open-v4.md#coche-real-y-registro-de-mejoras).

| Set / código archivado por ronda | Rondas | Válidas | Estado |
|---|---:|---:|---|
| std12-realcar-starts-v2-r1 | 3 | 2 | Parcial; no comparar como set completo |
| std12-realcar-starts-v2-r2 | 12 | 10 | Completo |
| std12-realcar-starts-v3-r1 | 12 | 12 | Completo |
| std12-realcar-starts-v4-r1 | 12 | 12 | Completo |
| std12-realcar-symmetric-final-r1 | 12 | 3 | Completo |

## std12-realcar-starts-v2-r1

| Geometría / sentido | Puntos estimados | Tiempo sim / pared (s) | Válida | Fallos | Evidencia |
|---|---:|---:|---|---|---|
| square100 / CCW | 30 | 30.936 / 13.835 | sí | — | [ronda](20261008T062122Z-std12-realcar-starts-v2-r1-square100-ccw/round.json) |
| square100 / CW | 30 | 30.938 / 13.738 | sí | — | [ronda](20261008T062207Z-std12-realcar-starts-v2-r1-square100-cw/round.json) |
| square180 / CCW | 25 | 81.735 / 36.396 | no | rule_maximum, stop_observed | [ronda](20261008T062252Z-std12-realcar-starts-v2-r1-square180-ccw/round.json) |

## std12-realcar-starts-v2-r2

| Geometría / sentido | Puntos estimados | Tiempo sim / pared (s) | Válida | Fallos | Evidencia |
|---|---:|---:|---|---|---|
| square100 / CCW | 30 | 33.095 / 14.663 | sí | — | [ronda](20261008T062724Z-std12-realcar-starts-v2-r2-square100-ccw/round.json) |
| square100 / CW | 30 | 32.917 / 14.777 | sí | — | [ronda](20261008T062810Z-std12-realcar-starts-v2-r2-square100-cw/round.json) |
| square180 / CCW | 30 | 49.916 / 22.276 | no | no_contacts, min_inner_wall_clearance_m | [ronda](20261008T062857Z-std12-realcar-starts-v2-r2-square180-ccw/round.json) |
| square180 / CW | 30 | 49.516 / 22.054 | sí | — | [ronda](20261008T062950Z-std12-realcar-starts-v2-r2-square180-cw/round.json) |
| rect100x180 / CCW | 30 | 40.397 / 17.665 | sí | — | [ronda](20261008T063044Z-std12-realcar-starts-v2-r2-rect100x180-ccw/round.json) |
| rect100x180 / CW | 30 | 40.896 / 18.204 | sí | — | [ronda](20261008T063133Z-std12-realcar-starts-v2-r2-rect100x180-cw/round.json) |
| rect180x100 / CCW | 30 | 42.315 / 18.972 | sí | — | [ronda](20261008T063223Z-std12-realcar-starts-v2-r2-rect180x100-ccw/round.json) |
| rect180x100 / CW | 30 | 41.895 / 18.763 | sí | — | [ronda](20261008T063313Z-std12-realcar-starts-v2-r2-rect180x100-cw/round.json) |
| shift140 / CCW | 30 | 40.616 / 18.087 | sí | — | [ronda](20261008T063404Z-std12-realcar-starts-v2-r2-shift140-ccw/round.json) |
| shift140 / CW | 23 | 42.017 / 19.236 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T063453Z-std12-realcar-starts-v2-r2-shift140-cw/round.json) |
| east140x100 / CCW | 30 | 36.716 / 16.387 | sí | — | [ronda](20261008T063524Z-std12-realcar-starts-v2-r2-east140x100-ccw/round.json) |
| east140x100 / CW | 30 | 38.216 / 17.062 | sí | — | [ronda](20261008T063612Z-std12-realcar-starts-v2-r2-east140x100-cw/round.json) |

## std12-realcar-starts-v3-r1

| Geometría / sentido | Puntos estimados | Tiempo sim / pared (s) | Válida | Fallos | Evidencia |
|---|---:|---:|---|---|---|
| square100 / CCW | 30 | 33.416 / 14.827 | sí | — | [ronda](20261008T065241Z-std12-realcar-starts-v3-r1-square100-ccw/round.json) |
| square100 / CW | 30 | 33.596 / 14.843 | sí | — | [ronda](20261008T065327Z-std12-realcar-starts-v3-r1-square100-cw/round.json) |
| square180 / CCW | 30 | 53.516 / 23.638 | sí | — | [ronda](20261008T065413Z-std12-realcar-starts-v3-r1-square180-ccw/round.json) |
| square180 / CW | 30 | 51.016 / 22.652 | sí | — | [ronda](20261008T065508Z-std12-realcar-starts-v3-r1-square180-cw/round.json) |
| rect100x180 / CCW | 30 | 41.316 / 18.325 | sí | — | [ronda](20261008T065602Z-std12-realcar-starts-v3-r1-rect100x180-ccw/round.json) |
| rect100x180 / CW | 30 | 41.316 / 18.346 | sí | — | [ronda](20261008T065651Z-std12-realcar-starts-v3-r1-rect100x180-cw/round.json) |
| rect180x100 / CCW | 30 | 44.916 / 19.814 | sí | — | [ronda](20261008T065741Z-std12-realcar-starts-v3-r1-rect180x100-ccw/round.json) |
| rect180x100 / CW | 30 | 43.616 / 19.444 | sí | — | [ronda](20261008T065832Z-std12-realcar-starts-v3-r1-rect180x100-cw/round.json) |
| shift140 / CCW | 30 | 42.432 / 18.859 | sí | — | [ronda](20261008T065923Z-std12-realcar-starts-v3-r1-shift140-ccw/round.json) |
| shift140 / CW | 30 | 42.706 / 18.991 | sí | — | [ronda](20261008T070013Z-std12-realcar-starts-v3-r1-shift140-cw/round.json) |
| east140x100 / CCW | 30 | 37.716 / 16.765 | sí | — | [ronda](20261008T070104Z-std12-realcar-starts-v3-r1-east140x100-ccw/round.json) |
| east140x100 / CW | 30 | 39.395 / 17.540 | sí | — | [ronda](20261008T070152Z-std12-realcar-starts-v3-r1-east140x100-cw/round.json) |

## std12-realcar-starts-v4-r1

| Geometría / sentido | Puntos estimados | Tiempo sim / pared (s) | Válida | Fallos | Evidencia |
|---|---:|---:|---|---|---|
| square100 / CCW | 30 | 33.916 / 14.985 | sí | — | [ronda](20261008T071231Z-std12-realcar-starts-v4-r1-square100-ccw/round.json) |
| square100 / CW | 30 | 33.416 / 14.867 | sí | — | [ronda](20261008T071317Z-std12-realcar-starts-v4-r1-square100-cw/round.json) |
| square180 / CCW | 30 | 51.315 / 22.837 | sí | — | [ronda](20261008T071404Z-std12-realcar-starts-v4-r1-square180-ccw/round.json) |
| square180 / CW | 30 | 50.735 / 22.464 | sí | — | [ronda](20261008T071458Z-std12-realcar-starts-v4-r1-square180-cw/round.json) |
| rect100x180 / CCW | 30 | 40.216 / 17.868 | sí | — | [ronda](20261008T071552Z-std12-realcar-starts-v4-r1-rect100x180-ccw/round.json) |
| rect100x180 / CW | 30 | 40.316 / 17.943 | sí | — | [ronda](20261008T071641Z-std12-realcar-starts-v4-r1-rect100x180-cw/round.json) |
| rect180x100 / CCW | 30 | 44.115 / 19.692 | sí | — | [ronda](20261008T071730Z-std12-realcar-starts-v4-r1-rect180x100-ccw/round.json) |
| rect180x100 / CW | 30 | 43.216 / 19.256 | sí | — | [ronda](20261008T071821Z-std12-realcar-starts-v4-r1-rect180x100-cw/round.json) |
| shift140 / CCW | 30 | 42.015 / 18.677 | sí | — | [ronda](20261008T071912Z-std12-realcar-starts-v4-r1-shift140-ccw/round.json) |
| shift140 / CW | 30 | 43.016 / 19.123 | sí | — | [ronda](20261008T072002Z-std12-realcar-starts-v4-r1-shift140-cw/round.json) |
| east140x100 / CCW | 30 | 37.216 / 16.611 | sí | — | [ronda](20261008T072052Z-std12-realcar-starts-v4-r1-east140x100-ccw/round.json) |
| east140x100 / CW | 30 | 39.517 / 17.604 | sí | — | [ronda](20261008T072140Z-std12-realcar-starts-v4-r1-east140x100-cw/round.json) |

## std12-realcar-symmetric-final-r1

| Geometría / sentido | Puntos estimados | Tiempo sim / pared (s) | Válida | Fallos | Evidencia |
|---|---:|---:|---|---|---|
| square100 / CCW | 30 | 29.730 / 13.264 | sí | — | [ronda](20261008T051639Z-std12-realcar-symmetric-final-r1-square100-ccw/round.json) |
| square100 / CW | 30 | 30.034 / 13.373 | sí | — | [ronda](20261008T051724Z-std12-realcar-symmetric-final-r1-square100-cw/round.json) |
| square180 / CCW | 1 | 35.996 / 17.695 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T051808Z-std12-realcar-symmetric-final-r1-square180-ccw/round.json) |
| square180 / CW | 1 | 30.217 / 14.657 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T051837Z-std12-realcar-symmetric-final-r1-square180-cw/round.json) |
| rect100x180 / CCW | 25 | 71.236 / 32.262 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T051904Z-std12-realcar-symmetric-final-r1-rect100x180-ccw/round.json) |
| rect100x180 / CW | 30 | 35.830 / 15.973 | no | min_inner_wall_clearance_m | [ronda](20261008T051952Z-std12-realcar-symmetric-final-r1-rect100x180-cw/round.json) |
| rect180x100 / CCW | 25 | 71.875 / 32.152 | no | rule_maximum, stop_observed | [ronda](20261008T052040Z-std12-realcar-symmetric-final-r1-rect180x100-ccw/round.json) |
| rect180x100 / CW | 5 | 35.676 / 17.147 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T052127Z-std12-realcar-symmetric-final-r1-rect180x100-cw/round.json) |
| shift140 / CCW | 1 | 35.237 / 17.685 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T052155Z-std12-realcar-symmetric-final-r1-shift140-ccw/round.json) |
| shift140 / CW | 7 | 45.116 / 21.720 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T052225Z-std12-realcar-symmetric-final-r1-shift140-cw/round.json) |
| east140x100 / CCW | 30 | 33.115 / 14.777 | sí | — | [ronda](20261008T052300Z-std12-realcar-symmetric-final-r1-east140x100-ccw/round.json) |
| east140x100 / CW | 14 | 54.396 / 25.770 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m | [ronda](20261008T052346Z-std12-realcar-symmetric-final-r1-east140x100-cw/round.json) |
