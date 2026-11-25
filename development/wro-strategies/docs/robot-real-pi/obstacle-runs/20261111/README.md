# Obstacle en el coche, 11–12 nov 2026: de la primera ronda con 1:1 a salir del lote, 3 vueltas y aparcar

## Hasta dónde llegó (12 nov, 03:05)

Todo en el coche con robotek-learn (Obstacle v3, `car.launch`), engranajes 1:1, `motor_rps_per_mps` 8.0. Sin juez: los
puntos no están validados. Telemetría completa en el Pi (`~/runs/`); aquí, `events.jsonl` y `params.yaml` de las rondas
clave.

| Hito | Ronda | Resultado |
|---|---|---|
| Ronda completa sin lote | 00:02 (`20261112-000207`) | DONE 107,1 s, vueltas 36,2 / 33,1 / 33,8 s, sin recover |
| Salir del lote + 3 vueltas + aparcamiento parcial | 00:51 (`20261112-005114`) | DONE 111,6 s (vueltas 33,6 / 27,2 / 34,4 s), 26/26 señales por su lado, 3 `front_recover` al empezar cada vuelta junto al lote, parcial a 27° y a 9,5 cm de la línea del lote |
| **La mejor: lote + 3 vueltas + parcial** | **01:22 (`20261112-012236`)** | **DONE 105,9 s** del Start (vueltas 34,3 / 26,8 / 25,1 s, la 1 con la salida del lote), 19/19 señales pasadas `OK`, 5 `front_recover` en las curvas del lado norte, aparcamiento parcial (a 29°) |
| **Aparcado en paralelo** (solo aparcar, CCW) | **02:39 (`20261112-023916`)** | Parcial + los pulsos del entrenador `C+0.20 R-0.40 L-0.50 R+0.05 L-0.15 R+0.1 L-0.1`: paralelo dentro del lote según el entrenador (DONE 20,3 s) |
| Aparcar en CW | 02:46 (`20261112-024644`), 03:05 (`20261112-030500`) | **No sale**: la posición a lo largo de la recta falla 20–30 cm y cambia entre rondas. 02:46: terminó ~20 cm pasado el lote ([foto](cw-park-20261112-0246.jpg)); 03:05: empezó la entrada demasiado pronto y tumbó el límite izquierdo ([fotogramas del video](cw-park-20261112-0305-video.jpg)) |

Comandos (en el Pi, `~/robotek-learn`):

```bash
# Ronda completa: sale del lote, 3 vueltas, aparca con los pulsos (config guardada, robotek-learn c4a6daf)
bash tools/car-run.sh obstacle start_lot:=true strategy_params:=$HOME/robotek-learn/install/robotek_obstacle_v3/share/robotek_obstacle_v3/config/car_picam_park_round.yaml motor_rps_per_mps:=8.0 motor_min_rps:=2 recover_back:=0.3 lot_exit_speed:=0.2 lot_exit_steps:='L+0.25 R-0.3 L+0.25 R-0.3 L+0.25 R-0.3 C-0.2'
# Solo aparcar (el coche donde entraría a la recta de salida); direction:=cw|ccw evita esperar a las paredes
bash tools/car-run.sh obstacle strategy_params:=$HOME/robotek-learn/install/robotek_obstacle_v3/share/robotek_obstacle_v3/config/car_picam_park_test.yaml direction:=ccw motor_rps_per_mps:=8.0 motor_min_rps:=2
```

La ronda completa **con los pulsos del aparcamiento** (archivo `car_picam_park_round.yaml`) todavía no se corrió: el
paralelo de las 02:39 es de la prueba de solo aparcar.

### Qué se arregló esa noche (robotek-learn, de `e809b06` a `2404dbb`)

- **Grabación y logs como el Open:** `~/runs/<fecha>-obstacle-v3/` (telemetría a 25 Hz, eventos, escaneos, señales,
  parámetros); en la terminal, cada tramo con su tiempo, cada señal vista y pasada (`OK` / `WRONG SIDE`), `LAP`, la línea
  `ROUND`, los pulsos del aparcamiento y `STEER FAULT` / `CAMERA LOST`.
- **La dirección que no responde** (`steer_watch.py`, también en WRO-Strategies `02005cb`): todo el giro pedido y el
  giroscopio sin giro durante 0,5 s → para 0,6 s con las ruedas al centro. En el coche detectó el fallo (01:03: 14
  veces en la curva 6, el servo no volvió); lab sin fallo 195/200 igual, con fallo simulado 110 → 135/200.
- **El lote en las vueltas:** con `start_lot` las vueltas no sabían del lote (un pilar rojo en la recta de salida llevaba
  la línea al límite del lote); la zona del lote sale ahora de `park_lot_end` / `park_lot_length` (campo del equipo:
  0,31 / 0,3675 m; reglas 0,48) y en CCW también limita la salida de la curva 4.
- **`front_recover`:** con el morro más de 40° hacia el interior retrocede con el otro giro (maniobra de tres puntos);
  00:26: retrocedía a la derecha y deshacía el giro, cuatro veces.
- **La cámara "se paraba":** no era la cámara. En el Pi con 3 núcleos ocupados, de 27,6 imágenes/s sin comprimir
  (691 KB) llegaban 0,2/s a otro proceso; el JPEG de calidad 90 (82 KB) llega entero. El Obstacle lee ahora el JPEG;
  `rpicam-vid` muere con su nodo y `car-clean.sh` lo cierra. Si aun así la cámara falta más de 1,5 s, sigue con los
  colores que recuerda.
- **Aparcamiento:** el fijo (`park_mode` 1) en parcial (`park_fixed_partial`: aproximación, entrada en arco, recto,
  0,5 s más de retroceso con guardia) y después los pulsos fijos `park_finish_steps` (mismo formato que la salida del
  lote: R hacia la pared, L hacia fuera, + adelante, − atrás, segundos; en CW se invierten solos). Argumentos de
  `car.launch`: `park_finish_steps`, `park_pulse_speed`, `park_speed`, `park_align_speed`, `park_fixed_ahead`,
  `park_fixed_sense`, `park_lot_end`, `park_lot_length`, `direction`. Sin empujón ni pulsos automáticos del motor
  (con 1:1 sobra par).
- **CW, sin probar en el coche:** `park_fixed_sense:=2` busca los dos límites magenta como pareja (en una ventana de
  ±35 cm, separados el largo del lote ± 6 cm) y corrige la posición a lo largo de la recta hasta 40 cm. En el modelo,
  con la posición 25 cm mal en un sentido u otro, el coche termina en el mismo sitio en CCW y en CW; el modo 1 no
  veía ningún límite (banda de ±6 cm y los límites a menos de 0,16 m del LiDAR al pasar al lado).

### Qué le falta

Puntos del aparcamiento en las reglas (tabla de puntos, 1.8): salir del lote con al menos una vuelta 7, aparcado
entero y en paralelo **15**, aparcado en parte o no paralelo **7**. La ronda de las 01:22 ya cumple la salida del lote
(7) y un parcial (7); lo que más suma ahora es pasar del parcial al aparcamiento completo (+8), y que todo salga
también en CW.

| Falta | Por qué importa | Estado / siguiente paso |
|---|---|---|
| **Aparcar en CW** | El sentido lo decide el sorteo: sin CW, la mitad de las rondas no aparcan | La posición a lo largo de la recta falla 20–30 cm. Probar `park_fixed_sense:=2` en la prueba de solo aparcar y mirar `fix` / `seen` del evento `park_fixed` |
| **La ronda completa con los pulsos** | El paralelo de las 02:39 es de la prueba de solo aparcar; tras 3 vueltas el coche llega al lote desde otro sitio | Correr `car_picam_park_round.yaml` en CCW y en CW; si no queda igual, `park_fixed_sense:=2` y `park_align_speed` |
| **Aparcamiento completo y comprobado** | 15 en vez de 7: dentro entero y con las dos ruedas de un lado a menos de 2 cm de diferencia a la pared | Hoy el veredicto lo dice el entrenador mirando; medir con regla en cada prueba y, si es repetible, dejar la secuencia fija en los dos archivos |
| **El lote de la competición** | En el campo del equipo el lote está a 0,31 m; las reglas lo ponen pegado a la línea punteada (0,48) | Medir el lote el día de la competición y pasar `park_lot_end:=…` (y `park_lot_length` = 1,5 × el largo del coche) |
| **El servo que no gira a la izquierda** (curva 6) | 01:03: la dirección no respondió 25 s; la detección para el coche pero el servo no vuelve | Prueba con el coche levantado (invertir el giro 20 veces), mirar el tope del brazo a la izquierda, el cable y el conector |
| **Los `front_recover` del lado norte** | 3–5 por ronda en las curvas 5–6: tiempo perdido y riesgo de tocar pilares | Mirar en la telemetría por qué entra tarde a esas curvas (con 1:1 el coche gira distinto que el `real_v4` del lab) |
| **`motor_min_rps`** | Con 2 rps el coche no se queda parado, pero todo lo lento sube a 0,25 m/s | Decidir un valor para la competición; 1,6 rps se quedó parado una vez al arrancar con la dirección casi a fondo |
| **Los colores con JPEG en otra luz** | 19/19 señales bien a las 01:22 en casa; la luz de la competición es otra | Revisar los `sign seen … red/green` en la primera prueba allí |
| **Llevarlo a WRO-Strategies y al lab** | Allí solo está `steer_watch`: el lab no mide nada de lo de esta noche | La sesión que simplifica el v3 tiene el plan; pasar primero el lote en las vueltas y el aparcamiento con pulsos, y medirlos con `--car real_v4` |
| **Un perfil del lab con 1:1** | `real_v4` está ajustado con 54:30 | Medir rectas a 0,15 / 0,25 / 0,35 m/s con `motor_rps_per_mps` 8 y la LiDAR, y ajustar `real_v5` |

## Ronda completa, 12 nov 00:02 (`20261112-000207-obstacle-v3`)

Mismo comando (`bash tools/car-run.sh obstacle motor_rps_per_mps:=8.0`, 1:1, robotek-learn `e809b06`), salida fuera
del lote (`start_lot` 0), sin aparcamiento. «Ronda perfecta» según el entrenador; sin juez, los puntos no están
validados.

| | |
|---|---|
| Start → DONE (reloj del nodo) | **107,13 s** |
| Vueltas (parciales) | 36,18 / 33,10 / 33,84 s; de la vuelta 3 a DONE 4,01 s |
| Curvas | 12, la primera a los 4,9 s |
| Incidencias | un `WAIT_SENSOR` de 0,07 s a los 26,9 s (escaneo de 0,35 s de antigüedad); ningún recover |
| Distancias mínimas del LiDAR en RUN | frente 0,159 m, izquierda 0,133 m, derecha 0,121 m |

Es la mejor ronda completa con 1:1. La de 85,0 s del 8 nov era con 54:30 (otro coche: no se comparan).



## Choques de las 23:56 y 23:59

Primeras rondas del Obstacle v3 con los engranajes 1:1 y la grabación nueva (robotek-learn `e809b06`: telemetría,
eventos y escaneos en `~/runs/<fecha>-obstacle-v3/`). Comando:
`bash tools/car-run.sh obstacle motor_rps_per_mps:=8.0` (sin aparcamiento, sin salida del lote,
`car_picam.yaml`: `steer_limit` 0,3054). Sin juez: los puntos no están validados. Aquí van `events.jsonl` y
`params.yaml`; la telemetría y los escaneos están en el Pi (`~/runs/`) y en la Mac en `/tmp/obsrun/`.

| | 23:56 (`20261111-235642-obstacle-v3`) | 23:59 (`20261111-235929-obstacle-v3`) |
|---|---|---|
| Curvas 1–6 (desde Start) | 5,3 / 17,5 / 29,3 / 34,9 / 42,0 / 52,3 s | 5,6 / 16,1 / 27,6 / 33,1 / 40,3 / 50,6 s |
| Vuelta 1 | 37,6 s | 35,8 s |
| Qué pasó | Curva 6 lenta, `front_recover` a 0,12 m de la pared (58,0 s), otro a 64,0 s; el progreso salta a 16,0 (localización perdida) y se para a mano a 73 s | Choque en la curva 6 (`front_recover` a 55,2 y 55,9 s), parado a mano a 63,5 s |

## La dirección no siguió a la orden

Giro medido por el giroscopio (menos su sesgo) mientras la estrategia mandaba todo el giro (|steer| > 0,29 rad) a
0,15 m/s; lo esperado con la cinemática es ~0,40 rad/s.

| Ronda | Tramo | Orden | Giroscopio |
|---|---|---|---|
| 23:59 | curvas 1, 5 | todo a la izquierda | +0,35 / +0,29 rad/s |
| 23:59 | **curva 6, 51,4–55,0 s** | **todo a la izquierda, 3,6 s** | **−0,07 rad/s**: el coche siguió casi recto hasta la pared |
| 23:56 | curva 6, 51–58 s | todo a la izquierda | +0,30 rad/s |
| 23:56 | **62,8–63,4 s** | **todo a la derecha** | **+0,23 a +0,45 rad/s**: siguió girando a la izquierda |

- El 23:59 la orden pasó de todo a la derecha (48,0–48,2 s) a todo a la izquierda (51,4 s) y la izquierda no llegó;
  el 23:56 falló el paso de izquierda a derecha. Es el fallo de la dirección del Open de las 23:28 de ese día (una
  inversión de todo a un lado a todo al otro, el servo no se mueve) y del 4, 8 y 11 nov. La estrategia no lo causa;
  sin aclarar si es el servo, su conector, su alimentación o el tope mecánico del brazo de dirección.
- Comprobar con el coche levantado: invertir todo el giro varias veces seguidas (`tools/steer_calibration.py` o el
  teleop) y mirar si las ruedas siguen; tocar el conector del servo y medir la tensión del servo mientras invierte.

## Lab con el coche nuevo (`real_v4`, 50 campos × 2 sentidos × semillas 0–1, Mac)

El lab del Obstacle acepta `--car real_v4` desde `fe14c11` (escaneo del LD19 de 0 a 2π, huecos del LiDAR,
`gyro_scale`). El v3 lee bien el escaneo de 0 a 2π.

| Coche | Sin aparcamiento | Con aparcamiento |
|---|---|---|
| `real_v3` | 192/200, 124,1 s | 125/200, 161,3 s |
| `real_v4` | 195/200, 123,5 s | 127/200, 159,5 s |
| `real_v4`, `gyro_scale=0.94` | 195/200, 123,5 s | 131/200, 159,1 s |

`real_v4` está ajustado con los engranajes 54:30; con 1:1 falta medir la respuesta a 0,15–0,35 m/s. El lab no tiene
el fallo de la dirección salvo con `--car-param no_turn_lock=N`.
