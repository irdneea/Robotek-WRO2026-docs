> Registro histórico del juez v1 a 10 Hz. Consultar la [revisión actual](realcar-open-history.md) para los puntos corregidos.

# Reajuste Open con el coche real

8 de octubre de 2026. **En curso.** Objetivo: tres vueltas, parada reglamentaria y
30 puntos estimados en menos de 30 s desde Start en square100, con GUI, modo
honesto y máximo simétrico equivalente ±17,6°. El control usa solo LiDAR,
giroscopio y cámara con ruido. La pose real se graba aparte para el juez.

[Mejor ronda observada y por qué se elige](best-realcar-open-round.md).

## Modelo y estrategia

- Motor con tabla de batería baja; 0,60 m/s al 100 % es inferido. Se corrigió la
  extrapolación por encima del 100 % PWM (límite de comando 1,28 m/s). En los
  diagnósticos base y tune1–3 el límite se aplicó antes de la rampa; desde tune4
  se aplica después, como en `base_adapter`. Los candidatos comandan como máximo
  1,28 m/s, así que esa diferencia no les añade velocidad.
- Ganancia del plugin 20: permite seguir el servo medido. El primer diagnóstico
  nuevo usó 1 y añadió una respuesta artificialmente lenta; no sirve para
  comparar rendimiento con los siguientes.
- Perfil candidato `open_realcar_v1.yaml`, separado de `open_sensors_v1.yaml`.
  Carril interior limitado por el ancho observado del corredor, anticipación
  que requiere ver el extremo de la isla, y arco planificado con velocidad
  real estimada (0,60/1,28 y 0,42/0,60 para la última curva).
- La percepción descarta muros que continúan fuera de la ventana LiDAR y
  puntos aislados del muro exterior alineados con la isla.
- Frenada tras la última curva, manteniendo el servo bajo control con un
  comando dentro de la banda muerta del motor; DONE se publica después de
  esperar la frenada. Ese tiempo cuenta en la ronda.

## Diagnósticos por ronda

Diagnósticos para localizar fallos; comparar perfiles solo con el set estándar.
Tiempo **Gazebo / pared**, desde Start hasta el final que identifica el juez.
En intentos incompletos incluye el final de grabación, no un final reglamentario.
DONE o doce giros no aseguran vueltas puntuables ni una parada válida.

| Intento y evidencia | GUI | Puntos estimados | Tiempo sim / pared (s) | Válida | Margen mínimo (cm) |
|---|---|---:|---:|---|---:|
| [realcar-symmetric-base-sq100-ccw](20261008T043552Z-realcar-symmetric-base-sq100-ccw/round-judge-v1.json) | no | sin evaluar | desconocido | no | desconocido |
| [realcar-symmetric-base-sq100-ccw](20261008T043613Z-realcar-symmetric-base-sq100-ccw/round-judge-v1.json) | no | 27 | 52.731 / 23.557 | no | 0.15 |
| [realcar-symmetric-tune1-sq100-ccw](20261008T044016Z-realcar-symmetric-tune1-sq100-ccw/round-judge-v1.json) | no | 27 | 41.354 / 17.934 | no | 29.99 |
| [realcar-symmetric-tune2-sq100-ccw](20261008T044430Z-realcar-symmetric-tune2-sq100-ccw/round-judge-v1.json) | no | 30 | 34.676 / 15.370 | sí | 16.18 |
| [realcar-symmetric-tune3-sq100-ccw](20261008T044553Z-realcar-symmetric-tune3-sq100-ccw/round-judge-v1.json) | no | 2 | 33.816 / 16.181 | no | -0.69 |
| [realcar-symmetric-tune4-sq100-ccw](20261008T044729Z-realcar-symmetric-tune4-sq100-ccw/round-judge-v1.json) | no | 4 | 40.775 / 19.104 | no | -2.82 |
| [realcar-symmetric-tune5-sq100-ccw](20261008T044831Z-realcar-symmetric-tune5-sq100-ccw/round-judge-v1.json) | no | 2 | 34.635 / 15.627 | no | -3.74 |
| [realcar-symmetric-tune6-sq100-ccw](20261008T045035Z-realcar-symmetric-tune6-sq100-ccw/round-judge-v1.json) | no | 30 | 33.716 / 15.002 | sí | 12.94 |
| [realcar-symmetric-tune7-sq100-ccw](20261008T045154Z-realcar-symmetric-tune7-sq100-ccw/round-judge-v1.json) | no | 6 | 64.816 / 28.922 | no | -0.82 |
| [realcar-symmetric-tune8-sq100-ccw](20261008T045413Z-realcar-symmetric-tune8-sq100-ccw/round-judge-v1.json) | no | 30 | 30.516 / 13.537 | sí | 8.51 |
| [realcar-symmetric-tune9-gui-sq100-ccw](20261008T045536Z-realcar-symmetric-tune9-gui-sq100-ccw/round-judge-v1.json) | sí | 15 | 64.496 / 65.503 | no | 4.65 |
| [realcar-symmetric-tune10-gui-sq100-ccw](20261008T045825Z-realcar-symmetric-tune10-gui-sq100-ccw/round-judge-v1.json) | sí | 30 | 30.016 / 30.490 | sí | 1.99 |
| [realcar-symmetric-tune11-gui-sq100-cw](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/round-judge-v1.json) | sí | 9 | 64.296 / 65.244 | no | 6.36 |
| [realcar-symmetric-tune12-sq100-cw](20261008T050440Z-realcar-symmetric-tune12-sq100-cw/round-judge-v1.json) | no | 30 | 34.017 / 14.836 | sí | 22.16 |
| [realcar-symmetric-tune13-sq100-cw](20261008T050707Z-realcar-symmetric-tune13-sq100-cw/round-judge-v1.json) | no | 30 | 30.217 / 13.428 | sí | 8.65 |
| [realcar-symmetric-tune14-gui-sq100-cw](20261008T050840Z-realcar-symmetric-tune14-gui-sq100-cw/round-judge-v1.json) | sí | 30 | 30.080 / 30.555 | sí | 7.68 |
| [realcar-symmetric-tune15-gui-sq100-cw](20261008T051135Z-realcar-symmetric-tune15-gui-sq100-cw/round-judge-v1.json) | sí | 30 | 29.714 / 30.204 | sí | 8.24 |
| [realcar-symmetric-final-r1-gui-sq100-ccw](20261008T051335Z-realcar-symmetric-final-r1-gui-sq100-ccw/round-judge-v1.json) | sí | 18 | 64.796 / 69.031 | no | 6.70 |

El primer intento no arrancó por restricciones UDP del sandbox: sin Start
ni muestras, sus puntos y tiempos son desconocidos. Todos los fallos quedan
guardados y se explican en el [historial](realcar-open-history.md).

## Set estándar y repeticiones

Seis campos × dos sentidos, con el mismo motor saturado, sensores honestos,
ganancia 20, dirección automática y reloj de simulación. El ruido cambia entre
ejecuciones; una ronda válida de 29,7 s no garantiza repetir ese tiempo.
Los lotes en curso aparecen conforme terminan las rondas.

| Lote | Rondas terminadas / 12 | Válidas | Válidas bajo 30 s |
|---|---:|---:|---:|
| realcar-symmetric-final-r1 | 12 | 3 | 1 |
| realcar-symmetric-base-r1 | 8 | 0 | 0 |

| Lote y evidencia | Campo / sentido | Puntos estimados | Start → fin sim / pared (s) | Válida | Validaciones fallidas |
|---|---|---:|---:|---|---|
| [realcar-symmetric-final-r1](20261008T051639Z-std12-realcar-symmetric-final-r1-square100-ccw/round-judge-v1.json) | square100 / CCW | 30 | 29.730 / 13.264 | sí | — |
| [realcar-symmetric-final-r1](20261008T051724Z-std12-realcar-symmetric-final-r1-square100-cw/round-judge-v1.json) | square100 / CW | 30 | 30.034 / 13.373 | sí | — |
| [realcar-symmetric-final-r1](20261008T051808Z-std12-realcar-symmetric-final-r1-square180-ccw/round-judge-v1.json) | square180 / CCW | 1 | 35.916 / 17.660 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T051837Z-std12-realcar-symmetric-final-r1-square180-cw/round-judge-v1.json) | square180 / CW | 1 | 30.216 / 14.657 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T051904Z-std12-realcar-symmetric-final-r1-rect100x180-ccw/round-judge-v1.json) | rect100x180 / CCW | 25 | 70.832 / 32.077 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T051952Z-std12-realcar-symmetric-final-r1-rect100x180-cw/round-judge-v1.json) | rect100x180 / CW | 30 | 35.830 / 15.973 | no | min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T052040Z-std12-realcar-symmetric-final-r1-rect180x100-ccw/round-judge-v1.json) | rect180x100 / CCW | 25 | 71.455 / 31.968 | no | rule_maximum, stop_observed |
| [realcar-symmetric-final-r1](20261008T052127Z-std12-realcar-symmetric-final-r1-rect180x100-cw/round-judge-v1.json) | rect180x100 / CW | 5 | 35.616 / 17.120 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T052155Z-std12-realcar-symmetric-final-r1-shift140-ccw/round-judge-v1.json) | shift140 / CCW | 1 | 35.236 / 17.685 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T052225Z-std12-realcar-symmetric-final-r1-shift140-cw/round-judge-v1.json) | shift140 / CW | 7 | 45.036 / 21.683 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-final-r1](20261008T052300Z-std12-realcar-symmetric-final-r1-east140x100-ccw/round-judge-v1.json) | east140x100 / CCW | 30 | 33.115 / 14.777 | sí | — |
| [realcar-symmetric-final-r1](20261008T052346Z-std12-realcar-symmetric-final-r1-east140x100-cw/round-judge-v1.json) | east140x100 / CW | 14 | 54.376 / 25.761 | no | rule_maximum, stop_observed, no_contacts, min_inner_wall_clearance_m |
| [realcar-symmetric-base-r1](20261008T052440Z-std12-realcar-symmetric-base-r1-square100-ccw/round-judge-v1.json) | square100 / CCW | 27 | 43.555 / 19.305 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T052530Z-std12-realcar-symmetric-base-r1-square100-cw/round-judge-v1.json) | square100 / CW | 27 | 41.630 / 18.517 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T052620Z-std12-realcar-symmetric-base-r1-square180-ccw/round-judge-v1.json) | square180 / CCW | 27 | 50.296 / 22.313 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T052713Z-std12-realcar-symmetric-base-r1-square180-cw/round-judge-v1.json) | square180 / CW | 27 | 47.933 / 21.340 | no | rule_maximum |
| [realcar-symmetric-base-r1](20261008T052806Z-std12-realcar-symmetric-base-r1-rect100x180-ccw/round-judge-v1.json) | rect100x180 / CCW | 27 | 45.651 / 20.278 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T052858Z-std12-realcar-symmetric-base-r1-rect100x180-cw/round-judge-v1.json) | rect100x180 / CW | 27 | 45.256 / 20.187 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T052949Z-std12-realcar-symmetric-base-r1-rect180x100-ccw/round-judge-v1.json) | rect180x100 / CCW | 27 | 45.956 / 20.510 | no | rule_maximum, stop_observed |
| [realcar-symmetric-base-r1](20261008T053040Z-std12-realcar-symmetric-base-r1-rect180x100-cw/round-judge-v1.json) | rect180x100 / CW | 27 | 45.996 / 20.559 | no | rule_maximum, stop_observed |

**Límite físico:** square180 tiene una isla de perímetro 7,2 m. Tres vueltas
a 0,60 m/s necesitan al menos 36 s incluso como punto sin carrocería, antes
de calibrar, acelerar y frenar. El objetivo de 30 s se evalúa en square100;
no se atribuye a todas las geometrías del set.

## Verificación y límites

Pruebas funcionales de Open, evaluación y hardware ejecutadas tras compilar.
Se conserva `round.json`, ledger, parámetros, telemetría, sensores y copias del
código por intento. Los resultados son estimaciones de simulación; batería,
velocidad máxima y juego de dirección del coche real siguen pendientes de medir.
