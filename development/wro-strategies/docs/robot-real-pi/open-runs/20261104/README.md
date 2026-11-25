# Open v5 en el coche real, 4 nov 2026: el motor a 6 rps no mueve el coche

Dos pruebas del Open v5 de robotek-learn (`e296c62`) en el coche, en el campo del usuario, con el servicio de arranque
(`tools/car-autostart.sh`, `car.launch.py strategy:=robotek_open executable:=open_v5 motor_max_rps:=6`), con botón.
Batería 7,2–7,5 V. **No son rondas puntuables**: se pararon a mano (la 1) o se cortaron (la 2) sin terminar una vuelta.
No se midió la posición de salida (x, y, yaw) ni el tiempo oficial.

| Prueba | Datos | Duración | Resultado |
|---|---|---|---|
| 1 | `20261104-141436-open-button` (bag, log) + `20261104-141442-open-v5` (telemetría) | 30,6 s desde Start | parada con el botón en la primera curva; 0 giros |
| 2 | `20261104-141809-open-button` + `20261104-141813-open-v5` | ~50 s | 1 giro completado (23 s para la curva) |

Los bags y la telemetría están solo en local (`.gitignore`); aquí, los logs y los eventos.

## Lo que se vio

- **El motor recibió 6 rps todo el tiempo**: `/rrc/set_motor` = −6,00 (el signo es el del montaje) desde ~1 s después
  de Start, salvo cuando el v5 frenaba ante una pared. La estrategia pedía 1,28 m/s.
- **El coche avanzó a tirones**: rachas de 0,2–0,4 m/s y pausas de 2–6 s casi paradas (0,01–0,03 m/s por el LiDAR;
  el giroscopio cae a ~2,8 °/s, que es vibración, frente a ~11 °/s cuando se mueve en la curva). Media ~0,1 m/s.
  - Prueba 1: de 2 a 10 s, la pared delantera se quedó a 1,33 m; en la curva, 7 s con todo el giro y solo 12° de rumbo.
  - Prueba 2: la curva de 90° tardó 23 s, con pausas en 6–8, 18–20 y 42–48 s.
- **La batería casi no baja** en las pausas (7,20–7,30 V con 6 rps mandados): el motor no está tirando de mucha
  corriente. Apunta a que la placa no lo está empujando, no a un motor bloqueado mecánicamente.
- **La dirección funciona como se manda**: centro 1403 µs, −17,6° → 1793 µs, proporcional en medio (`/rrc/acker_servo/set_state`).
  El v5 giró en la dirección correcta (CW) y terminó el primer giro en la prueba 2.
- **Sentido**: eligió CW en las dos (la cámara vio más naranja). Falta confirmar que era el sentido del campo.
- **LiDAR**: un par de huecos de 0,2 s y un aviso de «Stale LiDAR/IMU» en la prueba 2 (frena un ciclo); no explica las pausas.

## Hipótesis y siguiente prueba

La placa RRC Lite controla la velocidad en lazo cerrado con el encoder, con un modelo de motor (`motor_type`) que no se
envía (`controller_params.yaml`: `motor_type: -1`): usa el que tenga guardado, que no es el del motor 310 nuevo. Con el
encoder mal escalado el lazo puede quedarse corto o ir a golpes. (Con `motor_type 2` el 1 nov el motor arrancó solo y no
paraba con 0.) También puede ser un cable del encoder flojo.

Siguiente prueba, **ruedas en el aire**: 6 rps constantes durante 10 s, mirando si la rueda gira continua o a golpes; luego
lo mismo en el suelo. Si va a golpes, revisar el cable del encoder y averiguar el `motor_type` del 310 (código de
Hiwonder para el MentorPi) antes de tocarlo. Mientras el motor no sea fiable, no tiene sentido afinar el v5 en el coche.

## Prueba del motor sola (después de las rondas)

- La prueba manual del usuario (`ros2 topic pub /rrc/set_motor` con −4 y −7) **no vale**: con el servicio en marcha,
  `base_adapter` publica 0 en `/rrc/set_motor` a 50 Hz y pisaba los comandos (1 Hz).
- Con el servicio parado, solo `rrc_driver` y el LiDAR, y 6 rps mandados a 20 Hz (3 s adelante, 1 s parado, 3 s atrás;
  script en `/tmp/motor_test.py` del Pi): el coche **se movió a golpes también así**.
  - Adelante: ~1 m en 0,7 s (≈1,4 m/s, ~0,7 s después de mandarlo) y después **1,4 s quieto** con los 6 rps mandados
    (giroscopio en reposo, 2,8 °/s; distancia fija).
  - Atrás: 1,6 s quieto, luego ~1,2 m en 1,2 s, y siguió moviéndose ~1 s después de mandar 0.
  - La batería bajó solo a 7,22 V.
- Conclusión: el fallo está entre la placa y el motor (lazo de velocidad, encoder o conexión), no en el v5 ni en
  `base_adapter`. Cuando avanza, llega a más de 1 m/s; el problema son las paradas.

## Causa: el tipo de motor de la placa

- Prueba de potencia directa (paquete `0x05` como *duty*): la rueda no giró. En esta placa `0x05` es el tipo de motor
  (como dice `set_motor_type`), así que esa prueba dejó la placa en el tipo 1.
- Tipo 0 (JGB520) y −6 rps a 20 Hz durante 3 s, con la placa sola: **la rueda gira continua** (lo vio el usuario).
- Arreglo: `motor_type: 0` en `controller_params.yaml` de robotek-learn (`rrc_lite_driver`), que se envía en cada arranque.
- Pendiente: `motor_rps_per_mps` (4,8) se midió con el tipo anterior; hay que medir la velocidad real en el suelo con el
  tipo 0 antes de volver a correr el Open.

## Prueba 3, con `motor_type: 2` (15:45)

- Prueba de los cuatro tipos a 10 rps en el suelo (2 s adelante y atrás, placa sola): según el usuario, el **tipo 2
  (JGB27)** fue el que mejor avanzó; el 0 solo zumba en el suelo, el 1 y el 3 casi no se mueven. Al acabar las dos tandas
  el motor siguió girando con el tipo 0 puesto y 0 mandado hasta enviar 60 ceros seguidos (como con el tipo 2 el 1 nov).
- `motor_type: 2` en robotek-learn (`06a5728`), servicio de arranque con botón a 6 rps y bag aparte
  (`20261104-154420-open-button` + `20261104-154427-open-v5`).
- **No llegó a moverse**: Start a los 15:45:33 y parada con el botón 2,46 s después, aún en DETECT_DIRECTION; el motor
  recibió 0 todo el tiempo. Batería a **6,52–6,56 V** (frente a 7,2–7,5 V en las pruebas 1 y 2): el usuario la cambió.

## Prueba 4 y signo del motor (15:57–16:01)

- Antes de Start, `open_v5` se cayó (15:55:49) con un escaneo vacío en la odometría del LiDAR (`argmin of an empty
  sequence`): por eso el detector no se veía en RViz. Arreglo en `lidar_odometry.py` (robotek-learn `7d05d9d`,
  aquí `f58a088`): si uno de los dos escaneos tiene pocos puntos, usa el modelo.
- Prueba 4 (`20261104-155653-open-v5`, bag en `20261104-155403-open-button`): con +1,28 m/s mandados el coche fue
  **hacia atrás** (pared delantera de 1,39 a 1,97 m en 1,2 s); parada con el botón a los 13 s, sin giros válidos.
- Causa: `rrc_motor_sign: -1` se midió el 1 nov con el motor viejo en M4. Con el 310 en M1 y `motor_type: 2`,
  `/rrc/set_motor` +1 rps lleva el coche **hacia adelante** (comprobado a las 16:01, 2 s a +1 rps, lo vio el usuario).
  `rrc_motor_sign: 1.0` en robotek-learn (`546c759`).
- Pendiente: medir `motor_rps_per_mps` con el tipo 2 y el signo nuevo.

## Prueba 5: tres giros en 8 s y choque en la cuarta curva (16:02)

Open v5 con `motor_type: 2`, `rrc_motor_sign: 1`, 6 rps, con botón (`20261104-160116-open-v5`; bag en
`20261104-155403-open-button`, cortado al apagar el Pi y reindexado con `ros2 bag reindex`). Batería 7,45–7,52 V.
Sentido CW. No se midió la salida (x, y, yaw). **No es una ronda puntuable**: el usuario apagó el Pi a los ~21 s.

- **El motor ya va continuo**: 6 rps todo el tiempo y el coche avanza sin pausas. Velocidad real por el LiDAR ~0,65–0,72
  m/s en las rectas (la pared delantera baja 0,39–0,43 m en 0,6 s), frente a 1,25 m/s que pide el v5 con 4,8 rps por
  m/s: con el tipo 2 son **~8,5 rps por m/s** (por medir con calma).
- **Giros 1–3 bien**: a los 3,3, 5,9 y 8,0 s (2,4 s por tramo), el giroscopio hasta ~110 °/s en las curvas. El tercero
  terminó con el rumbo en −283° (≈13° de más).
- **Choque a los ~8,4 s**: tras el tercer giro, la distancia delantera cae a 0,12 m y el LiDAR se queda con ~93 puntos
  válidos de ~300 (tapado o pegado a la pared). El v5 entra en TURN a los 9,0 s, tarde. El freno de pared de
  `base_adapter` bajó el motor a ~1,4 rps y el coche se quedó 3 s quieto contra la pared (giroscopio en reposo).
- 12,5–14 s: gira y se suelta (¿lo movió alguien?); 14–18 s: otra vez 6 rps, con solo ~150 puntos en el LiDAR y de 16 a
  17 s quieto con 6 rps mandados (atascado). El bag termina a los 18,1 s, la telemetría a los 21,5 s.
- La carpeta `20261104-160200-open-v5` es del arranque siguiente (esperando el botón, la hora del Pi aún sin NTP).

Pendiente: por qué el v5 no frenó ni giró a tiempo en la cuarta curva (velocidad real distinta de la del modelo,
odometría con `motor_rps_per_mps` mal, LiDAR tapado); medir `motor_rps_per_mps` con el tipo 2; una marcha atrás o
parada cuando el coche se queda atascado contra la pared.

## Prueba 6: a 4 rps, 12 giros contados en 37 s con un atasco en la isla (16:09)

`motor_max_rps:=4`, `motor_type: 2`, `rrc_motor_sign: 1`, con botón (`20261104-160813-open-v5`; bag en trozos de 5 s en
`20261104-160806-open-button`). Batería 7,46–7,52 V. Sentido CW. No se midió la salida (x, y, yaw).

- El motor recibió 4,00 rps (se confirma en el bag), pero **la velocidad real casi no bajó**: ~0,72–0,81 m/s en las
  rectas, frente a 0,65–0,72 a 6 rps. Con el tipo 2, 4 rps ya está cerca del tope del motor 310 (0,70 m/s sin carga
  según `robot.yaml`). Para ir más despacio hay que bajar de verdad (2–3 rps) y medirlo.
- Giros 1–7 cada ~2,3 s (de 2,3 a 16,7 s). En el 8 empezó tarde (pared delantera a 0,33 m, pared exterior a 0,12 m a
  la izquierda) y **se quedó atascado de 21,3 a 26,5 s**: el LiDAR sin puntos a la izquierda (pegado a algo), rumbo fijo y
  el freno de pared de `base_adapter` dejando el motor a ~0,5 rps. Según el usuario, chocó con la isla central.
  A los ~26,5 s se soltó (no sabemos si lo movió alguien) y siguió.
- El v5 contó los 12 giros y pasó a DONE a los **37,0 s** desde Start (FINISH a los 36,1 s). **No es una ronda válida**:
  hubo choque y quizá ayuda; el tiempo incluye ~5 s atascado.
- Parada: el v5 se quedó en DONE con el motor a 0 (sin volver a arrancar).

Desde las 16:13 el v5 publica `/open/turn` para RViz (robotek-learn `1a3e875`, aquí `4b69db0`): rayo y umbral de la pared
delantera, la pared de la isla ajustada con su final y el look-ahead, y el texto «delante / isla / armado».

## Pruebas 7 y 8: a 2,5 rps (16:22 y 16:28)

`motor_max_rps:=2.5`, `motor_type: 2`, `rrc_motor_sign: 1`, con botón; bag en trozos en `20261104-161437-open-button`.
Batería ~7,5 V. No se midió la salida (x, y, yaw). Ninguna es una ronda válida.

- **Prueba 7** (`20261104-161443-open-v5`, 16:22:13): parada con el botón a los 4,9 s sin moverse. El Open no recibía
  la cámara desde las 16:15 (bag: ninguna imagen del detector desde entonces): la suscripción *best effort* de una imagen
  de 0,9 MB con el búfer de 208 KB del Pi perdía todos los fotogramas cuando el Pi iba cargado (load 8, en parte por un
  comando mío colgado). Arreglo: suscripción *reliable* (robotek-learn `8f124d6`); el detector pasó a 7–8 Hz.
- **Prueba 8** (`20261104-162648-open-v5`, 16:28): **eligió CW y la pista era CCW**. Al Start la cámara solo vio la
  línea naranja a lo lejos (O=101, B=0, `frames/detector-start-0.2s.jpg`); la azul, más cerca, salía blanca por el
  reflejo de la luz y no se detectó (a los 3,6 s sí: `frames/detector-3.6s.jpg`). Con CW el v5 espera la isla a la
  derecha: la derecha siguió a 0,34 m, la izquierda se abrió a 5,5 m a los 3,6 s (la curva era a la izquierda) y, sin
  «fin de isla», no giró: chocó de frente hacia los 5,5 s y siguió empujando hasta la parada (13,1 s).
- **Velocidad a 2,5 rps: ~0,45–0,5 m/s** (pared delantera de 1,05 a 0,56 m en 1,0 s), frente a ~0,75 m/s a 4 y 6 rps.

Pendiente de estrategia (no tocado): comprobar el sentido con el LiDAR en la primera curva (si se abre el lado contrario
a la isla esperada y el de la isla sigue cerca, el sentido está mal) y el reflejo sobre la línea azul en el detector.

## Prueba 9: con la comprobación de sentido, choque con la isla tras el segundo giro (16:45)

2,5 rps, `motor_type: 2`, comprobación del sentido con el LiDAR (robotek-learn `d15310e`), con botón
(`20261104-164407-open-v5`; bag en `20261104-164401-open-button`). Sentido CW, **esta vez correcto** (la comprobación no
actuó). La salida estaba cerca de la primera curva (pared delantera a 1,19 m). No es una ronda válida.

- Giros 1 y 2 a los 1,8 y 4,6 s, a ~1,5–2,0 rad/s con todo el giro (radio real ~0,25 m a ~0,45 m/s): el usuario los ve
  «muy rápidos».
- Tras cada giro el coche queda pegado a la isla (derecha): 0,43 → 0,15 m después del primero; 0,30 m al acabar el
  segundo (5,8 s) y a los ~6,3 s **choca con la isla** (LiDAR tapado, delante 0,18 m, derecha 0,14 m). Atascado de
  6,6 a 10,6 s con el rumbo fijo; luego se mueve (¿a mano?) y se paró con el botón a los 15,2 s.
- Hipótesis: el giro empieza en cuanto se abre la isla y con todo el giro a esta velocidad recorta la esquina de la
  isla; además `inner_gap` 0,25 m deja poco margen en el coche real. Probar `inner_gap` mayor (0,35) o un giro menos
  cerrado, primero en el lab.

## Prueba 10: `inner_gap` 0,35, el coche se queda parado en la primera curva (16:50)

2,5 rps, `motor_type: 2`, `strategy_params` con `inner_gap: 0.35` (robotek-learn `e1fc70f`), con botón
(`20261104-164857-open-v5`; bag en `20261104-164851-open-button`). Batería 7,07–7,20 V. No es una ronda válida.

- **El sentido era el correcto**: la cámara vio naranja primero (O=206, B=0) → CW, y a los 2,7 s se abrió la derecha
  (2,49 m) con la izquierda a 0,55 m: la curva era a la derecha. El usuario creyó que se había confundido de lado.
- **No giró y chocó de frente**: el v5 pasó a TURN a los 2,7 s (pared delantera a 0,81 m) mandando todo el giro a la
  derecha, pero el giroscopio no marca giro (−5 a +10 °/s) y a los ~3,5 s el acelerómetro da un golpe de 28 m/s²: chocó
  con la pared de enfrente, como vio el usuario. Después, quieto contra la pared con 2,5 rps hasta los ~8 s. (La
  «pared delantera fija en 2,43 m» de la telemetría se mide ya a lo largo del rumbo nuevo, a la derecha.)
- El servo no quedó grabado (`/rrc/acker_servo/set_state` no estaba en la lista del bag; añadido en robotek-learn
  `7f380a1`). Movido a mano después (16:53, por el SDK) **sí gira** a los dos lados. No sabemos si en la ronda no le llegó
  la orden o no tuvo fuerza (batería 7,07 V); en la prueba 9, 5 min antes, giró bien.
- Desde los 6,2 s, avisos de «Stale LiDAR/IMU» (el IMU dejó de llegar unos segundos; giroscopio 0,0 a los 8 s); luego
  alguien movió el coche (LiDAR a 5–6 m) y se paró con el botón a los 17,3 s.
- Siguiente: repetir grabando el servo y mirando las ruedas; revisar por qué se cortó el IMU (8–10 s sin mensajes de la
  placa).

## Prueba 11: sin botón, con el servo grabado; el giro 1 demasiado cerrado choca con la isla (16:56)

`tools/open-debug-run.sh motor_max_rps:=2.5 strategy_params:=…open_v5_car.yaml` (sin botón, debug), `inner_gap` 0,35;
`20261104-165612-open-debug` (bag con `/rrc/acker_servo/set_state`, `launch.log`) + `20261104-165620-open-v5`.
No es una ronda válida.

- **El servo responde**: 1391–1407 µs en la recta, **1793 µs (todo a la derecha) de 2,63 a 3,63 s** en el giro y vuelta
  a ~1350 µs. El coche giró (−1,85 rad/s) y terminó el giro 1 a los 4,0 s con el rumbo en −84°.
- **Giró demasiado cerrado**: nada más acabar, la pared delantera pasa de 2,0 a 0,37 m y la derecha (isla) a 0,29 →
  0,20 m; a los ~5,0 s el LiDAR queda tapado: **chocó con la esquina de la isla**. El usuario: «giró mucho en la primera
  curva». Atascado de 5 a 10 s (dirección a la izquierda para soltarse, giroscopio en reposo); luego varios intentos más
  y parada a los 26,3 s.
- Causa probable: el giro empieza en cuanto se abre la isla (a ~0,46 m de ella) y con todo el giro a ~0,45 m/s el radio
  es ~0,25 m: el coche pivota sobre la esquina de la isla y la recorta. En el simulador el mismo giro no choca.
- Siguiente: empezar el giro más tarde (dejar pasar la esquina de la isla) o limitar la dirección en el arco; el lab
  está probando `turn_front_distance` y `corner_lookahead`.

## Prueba 12: giro retrasado 0,15 m, sin batería (17:02)

`open-debug-run.sh` sin botón, `inner_gap` 0,35, `turn_delay_distance` 0,15 (`20261104-170220-open-debug`, bag cortado
por el apagado y reindexado + `20261104-170232-open-v5`). **No sirve para evaluar el giro**: la batería se agotó. El coche
casi no avanzó hacia la curva (la pared delantera nunca bajó de 1,19 m: pasó de 1,44 a 2,36 m en los primeros 11 s y
luego quedó fija), con huecos del LiDAR (lados en inf, el v5 manda 0) y avisos «Stale LiDAR/IMU»; el Pi se apagó.
Desde aquí `open-debug-run.sh` graba el bag en trozos de 5 s (robotek-learn `6df3809`).

## Prueba 13: giro retrasado 0,15 m, otro choque tras el giro 1 (17:10)

`open-debug-run.sh` sin botón, `inner_gap` 0,35, `turn_delay_distance` 0,15, 2,5 rps, batería 8,2 V
(`20261104-170926-open-debug` + `20261104-170938-open-v5`; LiDAR alrededor del giro en
`20261104-170938-open-v5/scans-corner1.png`). No es una ronda válida.

- El giro 1 empezó **más tarde**: pared delantera a 0,66 m (0,88 m en la prueba 11). Giro de 2,5 a 3,7 s a ~2,1 rad/s,
  rumbo final −93…−95° por el giroscopio; el ángulo de la pared derecha antes y después (9° → 12°) da ~93° por el LiDAR:
  el giro en sí es de ~90°, el giroscopio no se equivoca (IMU a 44 Hz, sin cortes).
- Tras el giro: izquierda a 0,23 m al final del arco, luego la derecha (isla) baja de 0,80 a 0,33 m y la pared
  delantera de 2,0 a 0,36 m en 0,9 s (más rápido de lo que avanza el coche: algo entra en la ventana de ±3°, probablemente la
  esquina de la isla). Choque a los ~4,9 s; el usuario: «giró mucho pero esta vez menos fuerte».
- Conclusión provisional: con el radio real (~0,25 m) el arco deja al coche mal colocado respecto a la isla, empiece antes
  o después. Afinar a ciegas en el coche no converge: esperar al perfil del coche real en el lab (sesión aparte) que
  reproduzca las pruebas 11 y 13.

## Análisis posterior: el yaw del v5 se queda corto porque el bucle va lento

Hecho con los bags y los escaneos de la telemetría, después de las pruebas.

- `/open/steer` (un mensaje por ciclo de control) iba a **38,8 Hz** en la curva 1 de la prueba 11 y a 38,6 Hz en la 9.
  En la prueba 6 iba a 48,6 Hz; esa prueba fue antes de los marcadores `/open/turn`. El nodo integra el giroscopio con
  `dt = 1/50` fijo, así que su yaw marca ~78 % del giro real.
- Prueba 11, curva 1: el giroscopio grabado suma ~118°, el rumbo según las paredes del LiDAR ~121° y el yaw del v5 91°. El
  coche salió de la curva apuntando ~30° hacia la isla y la siguió recortando.
- Rumbo de las paredes menos yaw del v5, tras cada curva: prueba 9, −16° y −12°; prueba 5, −6°, −15° y −14°; prueba 6,
  unos −3,5° por curva, que se acumulan hasta el atasco de la curva 8.
- El giro no es más cerrado que en el lab: 1,75 rad/s a ~0,62 m/s es un radio de ~0,37 m (17,6° con el wheelbase de
  0,119). El «radio 0,25 m» de arriba daba por hecho 0,45 m/s.
- Prueba 13 (37,9 Hz): las paredes del LiDAR dan ~33° de más tras la curva 1 (de −5° a −38° respecto del yaw del v5),
  no ~93°: la comparación de la pared derecha de arriba no lo vio. Es el mismo fallo.
- Perfil del lab que lo reproduce: `open_lab --car real_v2` ([open-estado.md](../../../open-estado.md), «Perfiles del
  coche en el lab»). En el lab, con el nodo viejo, `turn_delay_distance` 0,15 solo retrasa el choque, como en la prueba 13. Con el `dt`
  medido (`9ce7d67`) las rondas del campo clásico acaban sin tocar nada.

## Prueba 15: con el rumbo corregido, 12 giros y DONE en 28 s (17:28)

Tras apagar y encender el coche (la prueba de las 17:20 corrió con nodos sobrantes de la anterior: dos estrategias y dos
drivers de la placa; la de las 17:22 no se movió, con 105 avisos «Stale LiDAR/IMU»). `open-debug-run.sh` sin botón,
nodo con el `dt` medido (robotek-learn `8f638a4`), `inner_gap` 0,35, sin retraso del giro, 2,5 rps, bag ligero
(`20261104-172828-open-debug`, con `cpu.log`) + `20261104-172837-open-v5`. Sentido CW.

- **12 giros contados**, uno cada ~2,1 s (2,1 → 26,4 s), FINISH a los 27,0 s y **DONE a los 27,9 s** desde Start, con el
  rumbo integrado en −1088° (12 × 90° = 1080°). El usuario: «no completó pero dio más vueltas». Pendiente de confirmar con
  él qué faltó (dónde paró, si tocó). En los giros 11 y 12 la izquierda sale en inf un momento (posible roce con la pared
  exterior). Tras DONE el coche se movió a mano.
- Bucle de control a **39,4 Hz** (máx. 0,09 s entre ciclos) aun sin el JPEG ni `/open/turn` en el bag: el límite es el
  propio nodo (`open_v5` ~66 % de un núcleo en `cpu.log`; `battery_guard` ~36 %, `camera_publisher` ~29 %,
  `scan_adapter` ~27 %). Con el `dt` medido ya no afecta al rumbo.
- No es una ronda puntuable validada (sin posición de salida medida ni juez).
- **El rumbo real se va cerrando hacia la isla** (el usuario lo vio así). En cada recta comparé el rumbo real (ángulo de la
  pared exterior en el LiDAR) con el que cree el Open (giroscopio): `rumbo-por-recta.png` y `rumbo-deriva.png`.
  - Rectas 0–1: real ~0°. Recta 2: −6°; 3: −9°; 4: −13°; 5: −20°; 6: −25°; 7: −35°; 8: −38° (negativo = hacia la isla).
    El Open cree estar entre −1° y −8° todo el tiempo.
  - Unos **4–6° de más en cada giro**: el giroscopio marca ~5 % menos de lo que gira el coche, o tiene un sesgo que se
    acumula en los giros. El máximo medido fue de 1,68 rad/s, así que no es saturación del giroscopio.
  - Las rectas 9–11 tienen pocos ajustes válidos (2 escaneos) y no son fiables (el +37° de la recta 11 seguramente es
    otra pared).
- Siguiente: girar el coche a mano 4 vueltas completas en el suelo y comparar con el giroscopio integrado, para medir la
  escala; luego, o bien un factor de escala del giroscopio, o bien corregir el rumbo con la pared en las rectas
  (probarlo antes en el lab `real_v2`).

## Prueba 16: corrección con las paredes, salida mal colocada (17:42)

`wall_heading_gain` 0,3 (robotek-learn `8e3361f`), `inner_gap` 0,35, 2,5 rps, sin botón (`20261104-174225-open-debug`, en
el Pi). El usuario lo paró: el coche **no estaba bien puesto** en la salida y chocó. Intento mal preparado; no evalúa la
corrección.

## Prueba 17: corrección con las paredes, el coche se va recto contra la pared (17:45)

Misma configuración que la 16 (`20261104-174530-open-debug` + `20261104-174536-open-v5`). Chocó de frente con la
primera pared sin girar.

- **No es la corrección**: el Open se quedó casi sin ciclos de control. `/cmd_vel_raw` bajó de ~40 Hz a **4–14 Hz** desde
  los 2 s, con el giroscopio y el LiDAR marcados como «atrasados» (frena a 0 y el rumbo integrado se congela). Entre
  tanto el coche, con el último comando, siguió hasta la pared: las paredes muestran −2 → −13° de rumbo a los 2,5–4 s.
- Causa: **tres `round_reporter` sobrantes** de lanzamientos anteriores (19, 5 y 2 min), de 22 a 30 % de CPU cada uno;
  carga del Pi de 2 a 9,9. Ni mi parada ni la comprobación del script incluían `robotek_course`. Matados a mano; el
  script ya lo comprueba (robotek-learn, commit siguiente).
- Las pruebas 15 y 16 también corrieron con uno o dos de ellos: la 15 a 39 Hz.

## Prueba 18: con la corrección de las paredes, 12 giros rectos; choque al final porque el motor no frenó (17:52)

Con botón, servicio con `car-clean.sh` (robotek-learn `f0755ab`), `wall_heading_gain` 0,3, `inner_gap` 0,35, 2,5 rps,
batería 7,29 V (`20261104-175059-open-v5`; bag ligero en `20261104-175125-open-button`). Sentido CW.

- **El rumbo ya no se cierra**: en mitad de cada recta las paredes dan entre −5° y +1° (−10° una vez), frente a la deriva
  hasta −38° de la prueba 15. 12 giros, uno cada ~2,3 s, del 2,9 al 28,7 s; FINISH a los 28,8 s.
- **Choque al final**: en FINISH el v5 manda 0,15 m/s y a los 29,7 s 0 (motor 0,72 → 0 rps a los 29,9 s, comprobado en el
  bag), pero el coche **siguió a ~0,9 m/s sin frenar** (pared delantera de 1,97 a 0,27 m entre 28,9 y 30,9 s; odometría
  del LiDAR +1,6 m) y chocó con la pared de la zona de salida. Es el problema conocido del `motor_type: 2`: a veces el
  motor sigue girando tras mandar 0 (1 nov, pruebas de tipos de hoy).
- DONE a los 30,5 s desde Start (v5), con el coche aún en marcha. No es una ronda válida (choque, sin juez).
- Siguiente: frenar de verdad con el tipo 2 (p. ej. un pulso corto marcha atrás al pasar a 0, o otro tipo de motor/ajuste
  de la placa), probarlo con las ruedas en el aire primero.

## Freno con el motor tipo 2 (18:00–18:07)

Pruebas en el suelo con la placa sola (SDK), tras el choque final de la prueba 18:
- 2,5 rps 1 s y luego 0 / 0,25 s marcha atrás y 0: el coche chocó (el usuario: «mucho tiempo»). 2,5 rps 0,4 s: no se movió.
- 4 rps 0,4 s y luego 0, o 0,25 s marcha atrás a 4 rps y 0: **ninguno frenó** con 0.
- 4 rps 0,4 s, luego 1 s de un valor pequeño y 0 (vibración del IMU): +0,2 rps se desboca al llegar el 0; −0,2 rps se paró
  (aunque chocó con la pared, 1 s fue largo).
- Freno con el IMU (marcha atrás 0,5 rps solo mientras hay vibración, máx. 0,6 s): frena un momento y **se vuelve a
  desbocar** en cuanto vuelve el 0. El usuario: «no frenó».
- La documentación de la placa (wiki de Hiwonder, protocolo del RRC) solo tiene velocidad y «stop» por motor, y el stop
  del firmware es poner a 0 la consigna del PID: no hay modo libre ni freno ni PWM directo.
- Hipótesis: con el tipo 2 el lazo de velocidad de la placa tiene la realimentación al revés (el encoder cuenta en sentido
  contrario al que espera ese tipo): con consigna 0 cualquier giro le hace empujar más. Encaja con que el coche vaya a
  ~0,75–0,9 m/s con 2,5, 4 o 6 rps y con que acelere al pedirle menos en FINISH. Prueba propuesta: intercambiar los dos
  cables de potencia del motor en M1 (o A/B del encoder), tipo 2, ruedas en el aire: 2 rps y luego 0 debe parar y
  quedarse quieto (y `rrc_motor_sign` vuelve a −1).
- Prueba de 0 por tipo (18:08 y 18:10, placa sola, 6 rps 0,5 s y luego 0,25 s, después 2 s de 0): según el usuario
  **ningún tipo (0, 1, 3) se detuvo** con 0. El IMU sugería que el tipo 1 sí, pero el usuario lo vio seguir. Si ningún
  tipo sostiene el 0, el fallo no es el modelo de motor sino la realimentación del encoder (cable, pines o sentido del
  encoder del motor 310 nuevo), que afecta a todos los tipos. Pendiente: revisar el cable del encoder y cambiar los
  cables de potencia en M1; alternativa sin encoder: lazo abierto por el TB6612.
- Un solo 0 y luego nada (18:11:57): **tampoco frenó** (el usuario). El IMU marcaba reposo: el giroscopio no ve el avance
  en línea recta (solo giros y vibración), así que las lecturas de «parado» del IMU en estas pruebas no valen. Conclusión
  del día: el motor no frena con nada que mande el software; revisar encoder y cableado de M1.
- Comparación botón contra parada gradual, medida con el LiDAR (`car.launch.py teleop:=true motor_max_rps:=4`,
  `/cmd_vel_raw` y `/robotek/stop` desde un script):
  - Parada gradual (0,4 s a 0,6 m/s, 0,3 s a 0,15 y luego 0): **siguió 0,84 m en 2 s** tras la orden, hasta la pared.
  - Como el botón (0 de golpe), 0,4 s de empujón: el coche casi no había arrancado (2 cm).
  - Como el botón, 0,8 s de empujón: solo avanzó 4 cm en esos 0,8 s y, tras el 0, **retrocedió 0,17 m** solo en 3 s.
  - El motor no sigue las órdenes de forma reproducible: la misma orden da 0,5 m/s en una prueba y casi nada en otra, y
    con 0 se va hacia delante o hacia atrás. Refuerza la hipótesis del encoder/realimentación de M1. Hay que revisar el
    hardware antes de más pruebas en el suelo.
- Botón tras 1 s hacia delante (18:2x, mismo montaje): avanzó 0,12 m en el segundo; tras `/robotek/stop` siguió 9 cm
  hacia delante, se detuvo y **se desbocó marcha atrás: −1,36 m en 2 s (~0,8 m/s)** con 0 mantenido. El botón no frena
  distinto: la placa recibe el mismo 0. Es el comportamiento de un lazo de velocidad con la realimentación invertida o
  rota (el motor se dispara hacia cualquier lado con consigna 0). No probar más en el suelo hasta revisar M1.
- Igual con hasta 6 rps (`motor_max_rps:=6`, 1,5 m/s pedidos con la rampa de 1 m/s²): 0,12 m en el segundo; tras el
  botón, 7 cm más hacia delante y luego **18 cm marcha atrás** antes de quedarse quieto (de 1,0 a 1,5 s). Se repite el
  rebote hacia atrás tras el 0.
- Bajar la velocidad poco a poco (1 s a 1,5 m/s pedidos, luego de 0,6 a 0 m/s en 1,5 s y 0): **lo contrario de frenar**.
  Al empezar la bajada el coche aceleró (+0,26 m en 0,5 s, +0,86 m al acabar la rampa) y con 0 siguió a ~0,8 m/s:
  1,93 m en 3 s. Pedirle menos velocidad lo hace ir más rápido: la respuesta del lazo está invertida o desbocada.
- Placa reiniciada (interruptor; el Pi no se apaga) con `motor_type: -1` (tipo por defecto de la placa): 1 s adelante con
  signo +1 → **8 cm hacia atrás**, luego quieto con 0; con signo −1, 1 s y 2 s hasta ~10 rps → **no se mueve** (sin par).
  Con el tipo por defecto el 0 se respeta, pero no hay fuerza.
- Arrancar con el tipo 2 y frenar cambiando al tipo 0 (SDK + LiDAR, 4 rps 1 s): +0,19 m en el empujón, +5 cm tras el
  cambio y luego **0,45 m marcha atrás** con 0. Cambiar de tipo para frenar tampoco funciona.
- Tipo 2 para avanzar (4 rps 1 s), cambio al tipo 0 a la misma velocidad y bajada gradual a 0 en 1,5 s: **se desbocó
  hacia delante**, +2,17 m en 1,5 s tras el cambio, hasta la pared (estaba a 2,73 m). Desacelerar con el otro tipo
  tampoco frena.
- Adelante/atrás alternando (tipo 2, 4 rps 1 s; luego ±1,5 rps a 5 Hz durante 3 s y 0): +5 cm, luego **23 cm marcha
  atrás** en ~1,5 s y quieto desde los +2 s, también tras el 0 final (1,5 s). No se desbocó, pero tampoco se quedó en
  su sitio. La pared delantera estaba a 0,76 m.
- Más rápido y más suave (±0,8 rps a 12 Hz, 3 s, luego 0; pared a 1,61 m): +9 cm como máximo, vuelve a −5 cm y
  **queda quieto** desde los +2,5 s, también con el 0 final. El mejor freno del día; falta ver si se repite.
- Repetido dos veces: (1) +12 cm durante el vaivén y, ya con 0, **siguió avanzando hasta +31 cm**; (2) el empujón de 1 s
  ni lo movió (0 cm) y tras el 0 retrocedió 8 cm. **No es reproducible**: el vaivén no es un freno fiable. Con este
  motor y esta lectura del encoder, ninguna orden da un resultado repetible; hay que revisar el hardware de M1.
- Vaivén más corto (±1,0 rps a 10 Hz durante 1,5 s y luego 0), dos veces seguidas: (1) +13–14 cm y quieto (±3 cm);
  (2) +12 cm y quieto (±1 cm). **Dos de dos iguales**: pasa ~12 cm y se queda. Candidato a freno en el adaptador.
- Tercera vez igual: empujón +19 cm, luego +12–13 cm y quieto. **Tres de tres.**
- Freno ya en `base_adapter` (robotek-learn `c080c3b`), por el camino real (`/cmd_vel_raw` 1,5 m/s 1 s con la rampa
  de aceleración y `motor_max_rps:=4`, luego 0): **no frenó**, siguió despacio, +0,47 m en 3 s (~0,15 m/s). En las
  pruebas directas con el SDK (4 rps de golpe, sin rampa) sí paraba. Falta grabar qué llega a `/rrc/set_motor`.

## Prueba 19: con el freno de vaivén, 11 giros rectos y corte del USB de la placa en el último (18:57)

Con botón, `brake_rps` 1,0 (robotek-learn `c080c3b`, `brake_min_rps` 0,3 en `7b5a0b5`), `finish_speed` 0,4,
`finish_lead` 0,20, corrección con las paredes 0,3, 2,5 rps, batería 7,50 V (`20261104-185218-open-v5`; bag en
`20261104-185538-open-button`). Sentido CW.

- **11 giros**, uno cada ~2,2 s (2,1 → 24,6 s), rectas con las paredes entre −6° y +5° en mitad de recta.
- En el giro 12 (26,0 s), a los ~26,3 s **el USB de la placa se desconectó**: el kernel dice «usb2-port2: disabled by
  hub (EMI?), re-enabling» y la placa vuelve 1 s después como `ttyACM0`, pero `rrc_driver` murió (`TypeError` en
  `recv_task`, puerto cerrado). Sin IMU, el v5 frenó («Stale LiDAR/IMU») y el adaptador mandó el vaivén (−1/+1 rps)
  a nadie. **El coche se paró porque la placa se reinició**, no por el freno; quedó contra la pared delantera (0,15 m).
- Causa probable: ruido eléctrico (EMI) del motor o del servo a tope en el giro que tumba el USB de la placa. Es la
  misma pista que los cortes del IMU de antes («Stale LiDAR/IMU», pruebas 10 y 7).
- Siguiente: ferrita y cable USB corto y apantallado para la placa, separar el cable del motor; el driver debería
  reconectarse solo si el puerto cae.

## Freno por reset de la placa (19:05–19:14)

- La línea RTS del chip USB-serie de la placa (CH9102, `1a86:55d4`) está unida a su RESET: un pulso de 0,1 s la
  reinicia (el IMU se corta y vuelve ~2,6 s después, tras `enable_reception`). DTR no la reinicia.
- Con el SDK: 4 rps 0,6 s y reset por RTS → **el coche se paró** (el usuario).
- Integrado (robotek-learn `adfbffa`): `rrc_driver` escucha `/rrc/reset` (pulso RTS y, 2,5 s después, recepción, tipo de
  motor, offsets de servos y motores a 0); `base_adapter` con `brake_reset: true` lo publica una vez al parar después de
  moverse (fin del Open, botón, estop, watchdog).
- Por el camino real (1 s a 1,5 m/s pedidos con `motor_max_rps:=4`, luego 0): reset y **parado a +17 cm** en menos de
  0,5 s, quieto después. `finish_lead` del coche a 0,25 m para compensarlo.
- Prueba 20, **1 vuelta** (`laps: 1`, robotek-learn `e790b9e`) con el freno por reset (19:12): 4 giros y DONE a los
  13,1 s desde Start; el usuario: «funcionó perfecto» (paró en la zona de salida). `20261104-191140-open-v5`, bag en
  `20261104-191017-open-button`. (Antes, 19:10, una doble pulsación del botón paró el coche a los 2,7 s: el reset actuó.)
- **Prueba 21: primera ronda completa de 3 vueltas en el coche real** (19:14, con botón, freno por reset, corrección con
  las paredes, `inner_gap` 0,35, 2,5 rps, batería 7,49 V): 12 giros y **DONE a los 29,8 s** desde Start; el usuario:
  «terminó bien». `20261104-191256-open-v5`, bag en `20261104-191305-open-button`. Sin juez automático ni posición de
  salida medida: puntuación oficial pendiente de lo que anote el jurado.

## Rondas con arranque automático (19:21–19:34, sin bag)

- `20261104-192502-open-v5` (la «perfecta» de las 19:25): 12 giros (3,8 → 25,2 s) y DONE a los 28,3 s.
- `20261104-193339-open-v5` (19:33): 11 giros bien (2,9 → 24,7 s). En el **último giro** (26,4 s) el v5 manda todo el
  giro a la derecha, pero el giroscopio no marca giro y la odometría del LiDAR da ~1 m en línea recta en 1,1 s (~0,9 m/s,
  más rápido que en las rectas): **chocó con la pared** a los ~27,3 s, empujó quieto hasta los 31,7 s y a los 32,2 s
  giró (−2,2 rad/s), ya tarde. DONE a los 36,3 s. Igual que en la prueba 19 (también ~26 s, también el último giro): la
  placa dejó de obedecer dirección y velocidad unos segundos. Sin confirmar: el Pi se reinició después y el journal no
  es persistente, y el arranque automático no graba bag ni log en `~/runs`.

## Prueba 22: ronda completa grabada por el arranque automático (19:45)

Arranque automático con botón (robotek-learn `33d7f53` graba cada ronda; LEDs simples `b6fccf4`; reenvío del tipo de
motor `d8730aa`), freno por reset, corrección con las paredes 0,3, `inner_gap` 0,35, 2,5 rps.
`20261104-194323-autostart` (launch.log, kernel.log, bag desde Start) + `20261104-194328-open-v5`. Sentido CW.

- 12 giros (2,9 → 27,2 s, uno cada ~2,2 s); FINISH a los 27,2 s; **freno por reset a los 27,9 s**; DONE a los 31,0 s.
- Rumbo en mitad de recta (paredes): entre −0,6° y −7,2°, sin deriva entre la vuelta 1 y la 3.
- `kernel.log` vacío: **ningún corte del USB** de la placa. Los «Stale LiDAR/IMU» del log son al arrancar (antes del
  Start) y durante los 2,5 s del reset final, esperados.
- El usuario: «funcionó». Sin juez ni posición de salida medida.

## Cámara IMX708 (CSI) en el Open, coche quieto en la salida (21:00–21:45)

- **Colores:** la IMX708 ve el muro negro azulado (H ≈ 100, V 40–60), el naranja con H ≈ 7 y el rojo de un pilar con
  H ≈ 177. Los rangos medidos con la USB marcaban azul el pie del muro y naranja el pilar rojo. Los nuevos están en
  `~/.config/robotek/open_v5_car_picam.yaml` (robotek-learn d262bce).
- **Máscara del suelo:** se escapaba hasta arriba donde el pilar u objetos claros cortan el muro. Ahora esas columnas
  toman el borde de sus vecinas.
- **Desde la salida, a ~1,5 m:** a 640x360 las líneas tienen 1 px y casi no tienen color (la azul se ve gris marino).
  Con 1280x720 y la detección de líneas finas por contraste y tinte (`vision_line_contrast` 30, `vision_line_tint` 8)
  salen las dos enteras, sin falsos (B=130 O=273; robotek-learn c3fb320).
- **El sentido sale horario en esta salida antihoraria:** la regla elige la línea más larga en la imagen, y la azul
  queda partida por una junta del tapete. Se deja así: lo corrige la comprobación del LiDAR antes de la primera
  esquina (decisión del usuario).
- **Batería:** a 1280x720 y 15–30 fps el Open usaba 104–113 % de CPU y la batería se agotó. Ahora la cámara va a
  10 fps y solo funciona hasta elegir el sentido. CPU total del Pi: 42 % esperando el botón, 23 % después de Start;
  el detector es 2,6 veces más rápido con el mismo resultado (576877c).
- **LiDAR:** un corte de USB a las 21:06 lo devolvió como `/dev/ttyUSB1`; el launch del LD19 abre ahora
  `/dev/ldlidar`.
- **Pendiente:** una ronda con la IMX708. El arranque automático sigue con la cámara USB.

### Prueba 23: primera ronda con la IMX708 (21:50)

- **Ronda:** 12 giros, DONE 31 s después de Start, sin errores ni cortes de USB. Grabada en
  `~/runs/20261104-214804-picam/` (bag y logs) y `~/runs/20261104-214809-open-v5/` (telemetría).
- **Sentido:** la cámara eligió horario (cw, confianza 0,56–0,60). El LiDAR lo cambió a antihorario (ccw) antes de la
  primera esquina, como se esperaba. La cámara se apagó al pasar a FOLLOW.
- **No frenó al final:** el bag no tiene ningún `/rrc/reset`, y el motor bajó en rampa (2,2 → 0 rps) con 0 normales.
  A las 20:32 se había dejado en el Pi una prueba sin commit: el motor en M2 (`rrc_motor_port: 2`) y
  `brake_reset: false` («TEST on M2: plain 0»). Con el motor en M2, un 0 normal tampoco para el coche.
  `brake_reset` vuelve a `true` en el Pi (con M2); la copia de la prueba está en `/tmp/robot.yaml.m2-plain0`.

### Prueba 24: DIRECTION_FAULT, la cámara sin imagen (21:54)

- **Qué pasó:** después de Start se quedó 15 s en DETECT_DIRECTION y terminó en DIRECTION_FAULT, sin moverse.
  `rpicam-vid` llevaba todo el lanzamiento vivo sin dar ni un fotograma: «Camera frontend has timed out — check that
  your camera sensor connector is attached securely». Al relanzar daba 2 fps y fallaba, y el kernel avisó
  «rp1-cfe … stream on failed in subdev», con una traza en `cfe_stop_streaming`. Lo más probable es que el flex se
  moviera en la prueba 23.
- **Cambios** (robotek-learn b141292):
  - `pi_camera_publisher` reinicia `rpicam` si pasan 3 s sin fotograma y escribe su último ERROR en el log.
  - `start_button` ignora las pulsaciones de los primeros 5 s después del Start (`stop_lockout`), por si se pulsa
    dos veces sin querer.
- **Pendiente:** apagar el Pi del todo, volver a encajar el flex por los dos lados y arrancar.

### Prueba 25: el motor no mueve el coche (22:05–22:12)

- **La ronda:** con `direction_fallback: ccw` arrancó en antihorario y pasó a FOLLOW 2 s después del Start (la cámara
  daba imagen otra vez, tras volver a encajar el flex). El Open mandó 2,5 rps al motor en M2 a 50 Hz durante 19 s y el
  coche no se movió; los LED tampoco pasaron a azul. Se paró con el botón (el reset se mandó bien).
- **La placa directamente**, sin ROS:
  - funcionan los LED (magenta), la dirección (1250 → 1550 → 1403 µs), el IMU (31–48 Hz) y la batería (7,6 V);
  - con un pulso de 0,25 s a 2,5 rps, el IMU apenas registra el motor: en M2, aceleración +0,11 y giroscopio 2,1; en
    M1, después de volver a conectarlo allí, +0,04 y 1,8; en M3 y M4, sin motor, 0.
- **Lo que apunta:** el motor, su cable o su potencia, no la salida de la placa. El motor vuelve a M1
  (`rrc_motor_port: 1`, robotek-learn 7257a4d).
- **Pendiente:** con las ruedas en el aire, girar el motor 1 s para ver si gira, si zumba o si no hace nada.

### Prueba 26: el Open de la ronda perfecta, otra vez completo (22:15)

- **Configuración:** el arranque automático de la prueba 22: cámara USB, motor en M1, tipo 2 y freno por reset.
  `~/runs/20261104-221401-autostart/`.
- **Ronda:** 12 giros, reset al final y DONE 38 s después de Start, unos 7 s más que la 22. El motor vuelve a
  empujar: +0,35 de aceleración en 0,25 s, contra +0,05 de la prueba 25.
- **Sentido:** no había cámara USB (en `lsusb` solo están el LiDAR y la placa; `camera_publisher` falló 1200 veces
  seguidas). El sentido salió de `direction_fallback: ccw`, que era el correcto.
- **El botón:** se pulsó otra vez a los 2,2 s y a los 4,4 s del Start; las dos se ignoraron (`stop_lockout`).
- **Un reset de más a los 2,7 s:** el IMU de la placa dejó de llegar (hueco de 2,64 s desde t = 8,85 s). A los
  0,2 s el Open frenó por sensores viejos («Stale LiDAR/IMU»), y `base_adapter` lo tomó como una parada después de
  moverse: reinició la placa. El coche se quedó parado ~4 s (los 2,5 s de reconfiguración de la placa y sin IMU) y
  después siguió. Ese tiempo es lo que se perdió.
- **Cambios después de la prueba 26** (robotek-learn):
  - dfac27b: `status_leds` reenvía el color cada segundo.
  - 1fad3c5: el reset de la placa solo se hace al final (FINISH, DONE, OPERATOR_STOP, DIRECTION_FAULT), con el botón
    de parada o con el watchdog. Las demás paradas mandan 0.

### Prueba 27: el giro 9 no giró y el coche siguió recto contra la pared (22:22)

- **Ronda:** `~/runs/20261104-222028-autostart/`, telemetría `20261104-222033-open-v5`. Ocho giros bien (horario).
- **Giro 9** (t = 27,3 s): la dirección recibió lo mismo que en el giro 8, todo a la derecha (1793 µs a 50 Hz) y el
  motor a 2,5 rps.
  - En el giro 8, el yaw cambió 1,27 rad en 1 s.
  - En el giro 9, solo 0,1 rad en 1,2 s, y el LiDAR tampoco ve el coche girar: siguió recto.
  - A los 28,2 s el guardia de pared bajó el motor, pero a los 28,5 s chocó (pico de aceleración de 9,7).
- **Es el mismo fallo que la prueba 19 y la ronda de las 19:33:** el último giro no giró y el coche siguió recto.
  Las órdenes llegan a la placa, pero el servo no responde: el servo, su conector o su alimentación.
- **La batería:** 7,06 V con carga, frente a 7,6 V en la prueba 23.
- **Después del choque:** cortes del IMU de ~2,5 s a los 33, 38, 44, 65 y 75 s, sin ningún `/rrc/reset`. Parecen
  reinicios de la placa con el motor empujando contra la pared (sin comprobar). La ronda terminó con el botón.

### Prueba 28: no avanzó y después fue hacia atrás (22:31, primera con la IMX708 en el arranque automático)

- **Ronda:** `~/runs/20261104-223015-autostart/`, batería a 7,7 V. La cámara se apagó al pasar a FOLLOW.
- **0–15 s:** el motor recibió 2,5 rps en M1 (tipo 2) y el coche no avanzó.
- **A los 15,4 s:** el IMU se cortó 2,5 s sin ningún `/rrc/reset` ni corte de USB en el kernel: la placa se reinició
  sola. Un reinicio de la placa borra el tipo de motor.
- **A los 18 s:** la estrategia volvió a pedir 2,5 rps, y la placa, con el tipo por defecto, movió el coche hacia
  atrás. `resend_motor_type` solo reenvía el tipo con el motor parado, así que no lo corrigió.
- **El mismo launch tuvo 9 avisos «Stale LiDAR/IMU»**, también esperando el botón, con el coche quieto: la placa se
  reinicia sola a menudo. Las pruebas 25 y 27 también los tuvieron.
- **Cambio** (robotek-learn b4e2853): si los datos de la placa vuelven después de más de 1 s, `rrc_driver` reenvía en
  el momento el tipo de motor y los offsets del servo, también con el motor en marcha.
- **Pendiente:** la causa de los reinicios de la placa (alimentación o conector) y por qué el tipo 2 a veces no mueve
  el motor (pruebas 25 y 28).

### Prueba 29: ronda completa con la IMX708 en el arranque automático (22:37)

- **Ronda:** `~/runs/20261104-223410-autostart/`, telemetría `20261104-223416-open-v5`, batería a 7,6 V.
- **Sentido:** la cámara eligió horario (cw) y el LiDAR no tuvo que cambiarlo. La cámara se apagó al pasar a FOLLOW.
- **Recorrido:** 12 giros. FINISH a los 31,3 s de FOLLOW y motor a 0 a los 31,7 s, con un solo reset de la placa;
  después no se mandó nada más al motor. DONE a los 34,8 s.
- **Llegada:** paró con la distancia al frente a 1,65 m, frente a 1,67 m al salir (2 cm), centrado (0,48 / 0,51 m a
  los lados).
- **La placa se reinició sola esperando el botón** (corte de 2,5 s). `rrc_driver` lo detectó y reenvió el tipo de
  motor («Board data back after 2.5 s»), y el coche arrancó bien.
- **Puntos estimados: 30/30** (24 por secciones, 3 por vueltas, 3 por parar en la sección de llegada).
  - Es una estimación, no la decisión de un juez: no hay medida de contacto con las paredes ni validación de la
    sección de llegada.
  - Tiempo desde Start: ~32 s hasta la parada (reloj de pared; el Start fue ~0,5 s antes de FOLLOW).
