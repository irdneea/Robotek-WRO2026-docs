# Open en el coche, 11 nov 2026 22:23 y 22:24: dos rondas completas y comparación con el lab

Primeras rondas reales con el v5 simplificado (sin odometría, arco a giro completo, parada en seco al final;
robotek-learn `7b822a8` y `1ee969f`), driver nuevo del LD19 y engranajes 1:1. Sin juez: «ronda perfecta» según el
entrenador (3 vueltas, parada en la sección de salida). Los puntos no están validados.

| | Ronda 22:23 | Ronda 22:24 |
|---|---|---|
| Carpeta en el Pi | `~/runs/20261111-222318-open-v5` | `~/runs/20261111-222436-open-v5` |
| `motor_rps_per_mps` | 6,8 | **8,0** |
| Sentido | horario | horario |
| Start → DONE (reloj de pared) | 41,13 s | **34,78 s** |
| Vueltas (parciales) | 12,70 / 12,40 / 12,22 s | 10,66 / 10,70 / 10,62 s |
| Curva media | 1,16 s | 1,02 s |
| Recta media | 1,95 s | 1,64 s |
| Giro medio en curva (giroscopio) | 1,16 rad/s | 1,36 rad/s |
| FINISH → DONE | 3,41 s | 2,40 s |
| Parada respecto a la salida | 6,0 cm antes | 6,8 cm antes |
| LiDAR | 9,93 Hz, 0 huecos | 9,93 Hz, 0 huecos |

Campo medido con el LiDAR en las rectas: pasillos de 1,04 / 1,03 / 1,03 m y uno estrecho de 0,65 m (el este: la isla
`cNWWW` del lab). Salida de la ronda 22:24: frente 1,609 m, pared exterior 0,741 m, isla 0,300 m.

## La misma ronda en el lab

`open_lab`, isla `cNWWW`, horario, salida (0,236, −0,759), coche `real_v4` (con `stop_dead`), valores de
`car_picam.yaml`, 6 semillas. Script: la sección «Cómo repetirlo».

| | Coche (22:24, 8,0 rps por m/s) | Lab, giroscopio exacto | Lab, giroscopio al 94 % |
|---|---|---|---|
| Start → DONE | 34,78 s | 33,90 s | 33,98 s |
| Fin de vuelta 1 / 2 / entrada a FINISH | 11,00 / 21,70 / 32,32 s | 10,75 / 21,22 / 31,65 s | 10,88 / 21,35 / 31,97 s |
| Curva media | 1,02 s | 1,17 s | 1,25 s |
| Recta media | 1,64 s | 1,43 s | 1,38 s |
| Giro medio en curva | 1,36 rad/s (medido por el giroscopio) | 1,26 rad/s | 1,26 rad/s |
| FINISH → DONE | 2,40 s | 2,25 s | 2,0 s |
| Parada respecto a la salida | 6,8 cm antes | 0,7 cm antes | 0,1 cm antes |
| Resultado | 3 vueltas, parada dentro | 30 puntos, válida (6/6) | 30 puntos, válida (6/6) |

- **El total coincide al 2,5 %** (34,8 s frente a 33,9 s) y cada vuelta a 0,1–0,3 s.
- **El coche gira más cerrado y va algo más lento en recta que el modelo**: curvas un 13–18 % más cortas y rectas un
  15 % más largas. El `real_v4` se ajustó con los engranajes 54:30; con 1:1 el coche va más despacio y subvira menos.
- **Para 7 cm antes en el coche y casi en el punto en el lab**: el coche real frena más corto de lo que modela el lab.
  Queda dentro de la sección; `finish_lead` 0,14 → ~0,07 lo dejaría en el punto de salida.
- **Con 6,8 rps por m/s el coche va un 18 % más lento** que con 8,0 (41,1 s frente a 34,8 s): el valor bueno para 1:1
  es ~8 (la teoría daba 4,4 × 1,8 = 7,9). Ojo: 0,85 m/s × 8,0 = 6,8 rps, ya por encima del tope de 6,7 rps del Open,
  y el motor da ~7,5 vueltas/s sin carga: con 1:1 el coche va casi a su máximo.

## Ronda fallida anterior (22:11)

`~/runs/20261111-221122-open-v5`: la estrategia mandó 0,64–0,85 m/s y `base_adapter` −4,35 a −5,78 rps en M2 durante
28 s (grabado en la Mac), pero el motor no giró. El Pi se acababa de reiniciar. No se repitió en las dos rondas
siguientes; causa sin determinar (la placa recibió la orden).

## Cómo repetirlo

- Telemetría: copiar la carpeta del Pi y leerla con un script como `realround.py` (tiempos por estado, ancho de
  pasillo por recta, frente al salir y al parar).
- Lab: `lab.run_round(FIELDS/'../worlds-centres/cNWWW.sdf', 'cw', v5_factory(valores del coche), car=car_profile('real_v4'),
  spawn=(0.236, -0.759), trace=True)`.

## Choque de las 22:28 (ronda `20261111-222837-open-v5`)

Antihorario, isla cambiada (pasillos 1,04 / 0,60 / 0,62 / 1,03 m), 8,0 rps por m/s. Hizo la primera vuelta (11,0 s) y
chocó con la isla en la curva 5, a los 13,3 s. El detector de choques paró el coche y guardó `crash-222859.json`.

- **Qué pasó:** 0,74 s después de salir de la curva 4 la misión dio la isla por terminada a 0,19 m (dos escaneos
  seguidos) y giró. La isla seguía: el fin real estaba a 0,78 y 0,72 m.
- **Por qué:** un tramo de ~13 cm de la pared sur de la isla (x ≈ 0,45–0,58 m, la unión del panel añadido al alargar
  la isla) no devuelve nada al LiDAR: 11–17 rayos seguidos sin retorno, que se acercan al coche escaneo a escaneo.
  `_last_on_wall` contaba los rayos sin retorno como «fuera de la pared» y cortaba ahí. Con el pasillo siguiente
  estrecho, la pared de enfrente ya está a menos de 1,19 m ahí, así que el fin de la isla era la única condición
  que faltaba.
- **Arreglo (`scene.py`):** solo los rayos **con retorno** que ven más allá de la pared cuentan para terminarla; un
  tramo sin retorno no. Con los escaneos del choque: 0,78 y 0,72 m en vez de 0,19. Prueba nueva
  (`test_a_stretch_of_wall_with_no_return_is_not_the_island_end`), que falla con el código anterior.
- **Lab sin cambios:** 864/864 (9 salidas, giroscopio exacto), 857/864 al 94 %, 75 % con huecos, Gazebo 60/60 y
  324/324.
- En la primera vuelta el coche pasó por el mismo sitio sin fallar. **Corregido después (22:55):** lo más probable
  es que no fuera la pared sino datos perdidos del LiDAR; ver la sección de las 22:55.

## Roce con la pared exterior, 22:34 (ronda `20261111-223417-open-v5`)

Horario, isla con tres pasillos estrechos (1,03 / 0,63 / 0,62 / 0,60 m), 7,0 rps por m/s. Terminó (DONE, 12 curvas)
pero en 63,6 s: rozó la pared exterior en cada pasillo estrecho y se quedó trabado contra ella 3 s (43,5–46,5 s:
0,64 m/s mandados, frente fijo en 0,77 m, giroscopio en 0). Rectas de 7,5 s y 5,8 s, final de 6,2 s.

- **Por qué:** `inner_gap` 0,50 en un pasillo de 0,60 m. El coche iba a 0,43–0,48 m de la isla y la pared exterior
  quedaba a 0,12–0,20 m del LiDAR (0,12 es su mínimo; el coche mide 9 cm de medio ancho). Las rondas anteriores del
  día tenían un solo pasillo estrecho y ahí también iba justo (ronda 22:30: 0,61 m).
- **Arreglo (`mission.py`, `OUTER_GAP` 0,25):** en la recta el objetivo es el menor entre `inner_gap` y
  (ancho del pasillo − 0,25 m): en 0,6 m, ~0,35 m de la isla y 0,25 m (LiDAR) de la pared exterior. En pasillos de
  1 m no cambia nada.
- **Lab, 9 salidas:**

| Objetivo en pasillo estrecho | Giroscopio al 94 % | Margen p10 | Estrés con huecos |
|---|---|---|---|
| `inner_gap` siempre (antes) | 857/864 | 0,075 m | 75 % |
| Centro del pasillo | 864/864 | 0,075 m | 54 % |
| 0,20 m de la pared exterior | 864/864 | 0,081 m | 64 % |
| **0,25 m de la pared exterior (actual)** | **864/864** | **0,092 m** | 60 % |

  Con giroscopio exacto 864/864 (margen p10 0,110 m); modelo de Gazebo sin cambios (60/60, 41,92 s; 324/324).
  La prueba de estrés baja porque más cerca de la isla la mirada adelante se acorta y el giro empieza más tarde; el
  coche ya no tiene esos huecos (driver nuevo).
- Otras rondas de ese rato, todas completas: 22:30 (antihorario, 43,0 s) y 22:31 (antihorario, 37,5 s).

## Choque de las 22:48 y el fallo en sentido horario (ronda `20261111-224823-open-v5`)

Horario, tres pasillos estrechos, 8,0 rps por m/s, con `OUTER_GAP` ya puesto (isla a 0,39–0,41 m, pared exterior a
0,23 m: eso funcionó). Chocó con la pared exterior en la curva 2, a los 7,1 s.

- **Qué pasó:** las curvas empezaron con la pared de enfrente a 0,46 y 0,40 m, solo cuando el lado de la isla se
  abrió. El fin de la isla por delante no se vio en ningún escaneo (`island_end` = inf).
- **Por qué:** el LD19 del coche da ángulos de 0 a 2π. En horario `island_wall` usaba `bearing = -angles`
  (−2π a 0) sin envolver, y ningún rayo caía en la ventana de ±20° alrededor de +90°: **sin pared de la isla**, y
  por tanto sin mirada adelante y sin rumbo por la pared. En las rondas del día: antihorario, fin de isla y rumbo en
  casi todas las filas de FOLLOW; horario, en ninguna (0 de 233, 0 de 399, 0 de 364).
  - La mirada adelante nunca funcionó en horario en el coche (fallo antiguo): con pasillos de 1 m el giro tardío cabe.
  - El rumbo por la pared se perdió en horario desde que pasó a usar la recta de la isla (tercera pasada de la
    simplificación, `48cbe67`): `wall_heading()` sí envolvía los ángulos.
- **Arreglo (`scene.py`):** `bearing = arctan2(sin(sign·angles), cos(sign·angles))`. Con los escaneos del choque: fin
  de la isla de 0,80 a 0,31 m (habría girado ~26 cm antes) y rumbo −3° a −8°.
- **El lab no lo veía**: su escaneo es de −110° a +110° (el del LD19 de Gazebo). `real_v4` usa ahora el formato del
  coche (`scan_full_circle: true`, 504 rayos, 0 a 2π):

| 9 salidas, giroscopio al 94 % | Antihorario | Horario |
|---|---|---|
| Código anterior, formato del coche | 432/432 | **0/432** |
| Con el arreglo | 432/432 | 432/432 |

  Con el arreglo: 864/864 también con giroscopio exacto, 60 % en el estrés con huecos, modelo de Gazebo 60/60 y
  324/324. Prueba nueva con un escaneo de 0 a 2π en los dos sentidos (falla con el código anterior).
- Detector de choques: apagado por defecto en `car_picam.yaml` desde las 22:55 (pedido del entrenador);
  `detect_crash:=true` lo enciende.
- Pendiente: mirar el choque de las 22:44 (`20261111-224411-open-v5`, antihorario, 6 curvas).

## 22:55: falso choque por datos perdidos del LiDAR (ronda `20261111-225557-open-v5`)

Horario, con el arreglo del sentido horario (`4031a6f`): el fin de la isla se vio y la curva 2 empezó con la pared
de enfrente a 0,61 m (0,40–0,46 m en la ronda de las 22:48). A los 8,5 s el detector de choques paró el coche, pero
**no hubo choque**: iba recto (giroscopio ~0, dirección ~0, frente bajando normal de 1,72 a 0,99 m).

- **Qué disparó el detector:** escaneos con 50, 72, 140 y 145 rayos válidos. No son rayos sueltos: las vueltas llegan
  con un número de puntos equivocado (192, 226, 334, 446, 589 en vez de 504 ± 3), con sectores enteros vacíos e
  intervalos de 0,2–0,3 s. Se pierden paquetes en la línea serie del LD19.
- **Cuándo pasa** (vueltas con puntos de más o de menos, de la salida al final de cada ronda):

| Ronda | Vueltas malas | |
|---|---|---|
| 19:10, 22:23, 22:24, 22:27, 22:30, 22:44, 22:47, 22:48 | 0 | LiDAR perfecto |
| 22:31 / 22:34 | 2 / 1 | |
| **22:28** (choque en la curva 5) | **19 de 125 (15 %)**, desde los 8,7 s | |
| **22:55** (falso choque) | **27 de 75 (36 %)**, desde los 2,0 s | |

- **Corrección sobre el choque de las 22:28:** el «tramo de pared sin retorno» que tomé por la unión de un panel de
  la isla coincide con estas vueltas incompletas; lo más probable es que fuera la misma pérdida de datos y no la
  pared. El arreglo de `_last_on_wall` (un tramo sin retorno no es el fin de la isla) cubre los dos casos.
- `/dev/ldlidar` se volvió a crear a las 22:56 (el USB del LiDAR se reconectó). Sospecha: conector o cable USB del
  LiDAR flojo tras los golpes de la noche; sin confirmar. Comprobarlo con el coche parado y moviendo el cable:
  `bash tools/car-clean.sh && python3 tools/lidar-raw-check.py --seconds 30`.
- El detector de choques queda apagado por defecto (`a74ecca`): con datos perdidos del LiDAR da falsos positivos.

## 23:21, 23:26 y 23:28: dos rondas completas y un choque por la dirección

Con el arreglo del sentido horario (`4031a6f`), `OUTER_GAP` y el detector de choques apagado.

| | 23:21 | 23:26 | 23:28 |
|---|---|---|---|
| Carpeta | `20261111-232131-open-v5` | `20261111-232650-open-v5` | `20261111-232835-open-v5` |
| Sentido / pasillos | antihorario / 0,63–1,04–0,61–0,62 m | horario / 1,04 m los cuatro | horario / 1,04 m los cuatro |
| `motor_rps_per_mps` | — | — | 10,0 |
| Resultado | DONE, 12 curvas, **38,4 s** | DONE, 12 curvas, **31,2 s** | choque con la isla a los 20,9 s (9 curvas) |
| Vueltas | — | — | 9,9 s y 7,8 s |
| Curva / recta medias | 1,13 / 1,69 s | 1,03 / 1,26 s | 0,9–1,1 / 1,1 s |
| Parada respecto a la salida | 4 cm después | 0 cm | — |
| LiDAR | 9,94 Hz, 0 vueltas malas | 9,78 Hz, 0 malas, 5 pausas > 0,15 s | 9,79 Hz, 0 malas, 4 pausas |
| Fin de isla / rumbo por pared vistos en FOLLOW | 168 / 202 de 202 | 74 / 104 de 106 | 51 / 75 de 76 |

- **El arreglo del sentido horario funciona en el coche:** en horario ya se ven el fin de la isla y el rumbo por la
  pared (antes, 0 filas).
- **El choque de las 23:28 no es de la estrategia.** Al salir de la curva 9 el coche quedó ~9° pasado hacia la isla y
  la misión mandó corregir a la izquierda: pulsos del servo 1263 → 1078 µs (centro 1403) durante 1,07 s, grabados en
  la Mac. El giroscopio marcó −0,03 rad/s de media: **la dirección no fue a la izquierda** y el coche siguió recto
  hasta la isla. La placa no se reinició (sin avisos de `rrc_driver`).
- **Comparación de la respuesta a órdenes fuertes** (pulso < 1200 µs o > 1650 µs durante ≥ 0,4 s):

| Ronda | Izquierda fuerte: giro medio | Derecha fuerte: giro medio |
|---|---|---|
| 23:21 (antihorario) | 12 veces, +1,22 a +1,49 rad/s | — |
| 23:26 (horario) | 2 veces, +0,67 y +0,80 | 12 veces, −1,70 |
| 23:28 (horario) | 3 veces, +0,97 a +1,07; **la cuarta, −0,03** | 9 veces, −2,05 |

- Es el fallo intermitente de la dirección ya visto el 4 nov, el 8 nov y el 11 nov a las 17:59 y 18:01: la orden
  llega y el servo no se mueve. Esta vez justo en una inversión de todo a la derecha (1793 µs) a todo a la izquierda,
  con el motor acelerando de 0,64 a 0,85 m/s a la vez. Sin aclarar: servo, su conector o su alimentación.
- Con 10 rps por m/s el coche va más rápido (curvas a −2,05 rad/s frente a −1,70) y cada curva termina con una
  contra-corrección fuerte a la izquierda (3 de 3 antes del fallo; 2 en toda la ronda de las 23:26).

## 23:45: intento mal preparado, dos pilas a la vez (ronda `20261111-234508-open-v5`)

No es una ronda: 0 puntos, sin vueltas, parada del operador a los 112,7 s desde Start. Queda registrada como
intento mal preparado.

- **Qué pasó.** El Open se lanzó a mano a las 23:45 y a las 23:48 el arranque automático levantó otra pila con el
  Obstacle (`runs/20261111-234458-autostart`). Un solo Start (23:48:26) arrancó las dos estrategias.
- **Evidencia** (grabación de la Mac `~/rondas-coche/bags/20261111-162237-lidar-huecos`, relojes de la Mac y del Pi
  iguales): en `/robotek/state` aparecen los estados del Open (`CALIBRATE`, `DETECT_DIRECTION`, `FOLLOW`) y los del
  Obstacle (`SETUP`, `RUN`, `WAIT_SENSOR`) mezclados; `/cmd_vel_raw` alterna 0,85 y 0,0 m/s (10 273 mensajes en
  125 s: dos publicadores); `/rrc/set_motor` alterna -5,0 y unos -3 rps.
- **LiDAR.** Dos drivers leyeron el mismo puerto: en la telemetría del Open los escaneos llegan a 13,6 por segundo
  con 4 a 636 puntos (mediana 300) en vez de 10 por segundo con 504, y el LD19 escribió 137 veces
  `get ldlidar data is time out`. Antes de Start la mediana era 504.
- **El coche no avanzó.** La pared de frente se quedó en 1,68 m durante los 111 s de `FOLLOW` con 0,85 m/s pedidos
  (un solo valor de 0,64 m: algo pasó por delante). El giroscopio integró 0,15 rad en ese tiempo (sesgo).
- **Conclusión.** No dice nada de la estrategia. Es el caso de la nota «limpiar el coche antes de cada Open»
  (`tools/car-clean.sh`): un arranque automático vivo junto a un lanzamiento manual.
- **Límites.** No se sabe por qué el motor no movió el coche con órdenes de -3 a -5 rps (¿coche sujeto o levantado?,
  ¿las dos pilas reiniciando la placa?): no hay observación del operador anotada.
