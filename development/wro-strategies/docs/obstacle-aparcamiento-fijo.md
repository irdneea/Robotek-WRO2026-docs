# Obstacle v3: aparcamiento fijo (`park_mode: 1`, 8 nov 2026)

## Por qué

En el coche real del 8 nov (motor en M2 con control de velocidad, engranajes 54:30) el aparcamiento planificado de
`v3/park.py` no funciona:
- Son ~14 movimientos cortos de 3 cm a 0,06 m/s, y con todo el giro el motor no mueve el coche a esa velocidad.
- Con `motor_min_rps` 1,1–1,3 va a ~0,25–0,3 m/s, se pasa en cada movimiento corto (rueda 3–12 cm tras el 0) y
  acaba contra el límite de atrás. Dos veces se paró en el mismo sitio.
- Bolsas: `/tmp/obsrun/20261108-191940-obstacle-park-only/` y `20261108-192330-obstacle-park-only/` (solo en el Mac).
- En el lab con `--car real_v3` ya se veía: 8/200 con vueltas y aparcamiento ([obstacle-estado.md](obstacle-estado.md)).

## Qué hace

`src/robotek_obstacle/robotek_obstacle/v3/park_fixed.py` (`FixedParking`, hereda de `park.Parking`). Sin plan: cada
paso usa todo el sitio que tiene y **termina en un sensor**, no en un tiempo ni en una longitud:

1. **Aproximación:** adelante por una línea a 4 cm del lote hasta que `base_link` está `park_fixed_ahead` por delante del
   límite lejano (pose del LiDAR), alineado. Si se pasó, vuelve marcha atrás por la línea.
2. **Entrada:** marcha atrás con todo el giro hacia la pared hasta el rumbo `park_fixed_entry` (giroscopio), o hasta el
   guard.
3. **Bajada:** marcha atrás recta hasta el guard: la cola cerca de la pared o del límite cercano.
4. **Enderezar:** adelante y atrás alternando, con todo el giro y girando siempre hacia paralelo; cada movimiento
   termina en paralelo (giroscopio) o en el guard. Como mucho 24 movimientos.
5. **Centrar:** recto hasta el medio del lote (pose del LiDAR). Después, `PARKED` o `PARK_FAIL` (se queda donde está).

**Guard:** el contorno del coche, adelantado 2 cm más lo que rueda tras parar, a menos de `park_fixed_margin` de un
límite o de la pared, para el movimiento. El rodado se mide en cada parada (empieza en `park_fixed_roll`; se admiten
hasta 15 cm). Los objetivos de rumbo también se adelantan con ese rodado.

**Parámetros** (`v3/settings.py`; por defecto `park_mode: 0`, el planificador, sin cambios):

| Parámetro | Defecto | Qué es |
|---|---|---|
| `park_mode` | 0 | 1 = este aparcamiento |
| `park_fixed_ahead` | 0,145 m | dónde empieza la entrada, por delante del límite lejano |
| `park_fixed_entry` | 0,76 rad | rumbo que termina la entrada |
| `park_fixed_margin` | 0,012 m | margen del guard |
| `park_fixed_roll` | 0,012 m | rodado tras parar antes de medirlo (con piso de velocidad: ~0,08) |
| `park_lot_length` | 0,3675 m | entre las caras interiores de los límites (reglas: 1,5 × 0,245 m, el coche real medido el 9 nov; los números de esta página se midieron con 0,3495 m = 1,5 × 0,233 m) |
| `park_lot_depth` | 0,20 m | fondo desde la pared exterior |
| `park_lot_end` | 0,48 m | cara interior del límite lejano a lo largo de la recta de salida en CCW (en CW, simétrico) |

**El lote del campo del usuario aún no está medido.** Los tres `park_lot_*` sirven para ponerlo cuando se mida. El
aparcamiento planificado sigue usando el lote fijo de `obstacle_parking.py`.

## Lab (`real_v3`, solo aparcar)

Capas 0–49 × 2 sentidos × semillas 0–1 = 200 rondas:
- `obstacle_lab_suite.py --parking --param park_after=0 --car real_v3`;
- el coche sale de −0,25 m en la recta de salida;
- veredicto del juez: «aparcado del todo y paralelo».

Las rondas son inválidas por `rule_maximum` (no hay vueltas): solo cuenta el veredicto del aparcamiento.

| Variante | Fijo | Planificador (`park_mode: 0`) |
|---|---|---|
| **`real_v3`** | **195/200** (5 roces con un límite), 35,0 s | 35/200 (60 roces) |
| **Ronda completa: tres vueltas y aparcar** (`park_after` 24) | **145/200 aparcados; 138 válidas, 159 s** | 10/200; 8 válidas, 164 s |
| `park_speed` 0,04 / 0,10 | 199 / 104 | — |
| `park_fixed_margin` 0,008 / 0,016 | 156 / 153 | — |
| El coche cree el lote 1 cm antes / después (`park_lot_end` 0,47 / 0,49) | 156 / 184 | — |
| El coche cree el lote 1 cm más largo (`park_lot_length` 0,36) | 128 | — |
| `steer_gain=1.0` (radio 0,375 m, el otro extremo de la evidencia) | 103 | 140 |
| Piso de velocidad 0,25 m/s (`--car-param drive_min_speed=0.25`, como `motor_min_rps` 1,1) | **0** (`park_fixed_roll` 0,08) | **0** |
| Piso 0,12 / 0,16 / 0,20 m/s (`park_fixed_roll` 0,04) | 0 / 0 / 0 | — |
| Piso 0,12 / 0,20 / 0,25 m/s cortado en seco con el 0 (`drive_min_on_stop=0`) | 13 / 0 / 0 | 0 (con 0,25) |

**Ajuste** (semilla 0, 100 rondas por punto):
- `park_fixed_ahead` 0,10–0,20 × `park_fixed_entry` 0,55–0,85, y después una rejilla fina alrededor del mejor.
- Hay una franja buena: 0,145 m con 0,70–0,775 rad da 94–99/100; con 0,14 m, 87–92.
- A 1 cm de distancia cae deprisa: 0,13 m con 0,75 rad da 27; 0,16 m, 75.
- Con 0,20 m no aparca nunca.
- Con `steer_gain=1.0` (radio 0,375 m) lo mejor es 0,15 m con 0,65 rad (85/100) o 0,15 m con 0,85 rad (83/100), frente a
  78/100 de los valores por defecto en esa semilla. Si el coche gira más abierto, empezar ~0,5 cm más lejos con menos
  ángulo.

En la ronda completa los fallos que quedan vienen sobre todo de las vueltas (señales tocadas, `stop_observe`) y de
ese mismo margen de 1–2 cm de profundidad.

**Hallazgos:**
- **El fijo aparca mucho mejor que el planificador en este coche:** 195 frente a 35.
- **Es sensible a la geometría:**
  - 1 cm de error en la posición o el largo del lote cuesta 10–65 rondas.
  - Con un radio de giro distinto (`steer_gain=1.0`) cae a 103.
  - Antes de la prueba hay que medir el lote del campo. Si el coche gira más abierto de lo que dice `real_v3`, hay que
    reajustar `park_fixed_ahead` y `park_fixed_entry`.
- **Con cualquier piso de velocidad de 0,12 m/s o más no aparca ninguno de los dos** (casi todo roces). Tampoco si
  `base_adapter` cortara el motor en seco al recibir el 0, en vez de mantener el piso durante la rampa
  (`drive_min_on_stop=0`, opción del lab): el retraso de la placa (0,1 + 0,3 s) ya hace rodar demasiado. En un lote con 11,7 cm de holgura, un coche
  que rueda 8–12 cm tras cada parada no puede hacer movimientos cortos. En el coche hace falta ir despacio de verdad: el
  arranque y los pulsos de `base_adapter` (robotek-learn `7eb6ac9`) dieron 0,046 m/s con 0,06 pedidos, en recto. Pero
  con todo el giro, los pulsos de 0,66 rps y de 1 rps no lo movieron (`191115`, `191658`). A 0,04 m/s el lab da 199/200,
  y a 0,10 sin piso, 104. **Sin ≤ ~0,06–0,08 m/s reales con todo el giro, en el coche no hay aparcamiento**, ni el fijo
  ni el planificado. El arreglo es del motor: más reducción, o un control de la placa que dé fuerza a baja velocidad.
- Lo que no funcionó:
  - un paso para recuperarse cuando las dos marchas quedan bloqueadas lejos de paralelo: avanzaba ~1 cm y no ayudaba;
  - entradas de 0,95 rad: el coche se encaja en diagonal, con las dos esquinas contra los límites.

**Pruebas:** `src/robotek_obstacle/test/test_v3_park_fixed.py`. Comprueban:
- en el modelo cinemático con la ganancia de giro del coche, aparca en CCW;
- en CW y con 3 cm de rodado no toca;
- con 8 cm de rodado no toca;
- los `park_lot_*` mueven el lote.

## Prueba en el coche (solo aparcar, con bolsa)

El coche corre la copia de robotek-learn (`src/robotek_obstacle_v3/`, mismo `park_fixed.py`). Pasos y comando en
[robot-real-pi/obstacle-runs/20261108/README.md](robot-real-pi/obstacle-runs/20261108/README.md#aparcamiento-fijo-park_mode-1-prueba-propuesta).

## A ~0,3 m/s, compensando lo que rueda (8 nov, noche)

En el coche, los pulsos lentos no llevan la maniobra (22:44 y 22:48). Con `motor_min_rps` 1,1–1,3 continuo el coche
siempre se mueve, también con todo el giro. La prueba de frenada en el suelo (22:53, `lab-fit/brake_test.py`: 1,2 rps
durante 1,2 s y luego la parada) da:
- con un 0: 13–14 cm en recto y 0,18–0,22 rad con todo el giro;
- con un contragolpe de 2 rps durante 0,15 s: ~10 cm y 0,05–0,14 rad;
- repetible a ±1–2 cm.

**El lab con estos datos** (opciones de `real_car_v3.yaml`, apagadas por defecto):
- `real_v3` tal cual (prueba del SDK, sin rampa) rueda 9,4 cm en recto y 0,28 rad a tope; el coche, 13,4 cm y 0,20 rad.
- **Ajuste:**
  - `drive_gain=1.4`: la velocidad real es 1,4 veces la de la tabla.
  - `lock_speed_factor=0.6`: con todo el giro recorre 0,6 veces la distancia recta.
  - Resultado: 23,2 cm recorridos y 13,0 cm rodados en recto (coche: 23–26 y 13–14); con todo el giro, 0,42 / 0,23 rad
    (coche: 0,49–0,50 / 0,18–0,22).
- **El 0 de `base_adapter`:** el piso (`motor_min_rps`) se mantiene mientras la rampa baja a 0, así que en el lab rueda
  **27 cm** en recto y 0,48 rad. `drive_min_on_stop=0` (cortar en seco con el 0) lo deja como en la prueba del SDK.
- **Contragolpe** (`counter_speed` en m/s pedidos y `counter_s`): con 2 rps durante 0,15 s, el lab da 4,9 cm y 0,09 rad.
  El coche dio ~10 cm y 0,05–0,14 rad: **el lab lo sobrevalora en recto**.

**Aparcamiento fijo con piso de 0,25 m/s y el ajuste** (solo aparcar, capas 0–49 × 2 × semillas 0–1). Cada celda es
«aparcado del todo / roces»:

| Parada | `park_fixed_roll` 0,04 | 0,08 | 0,13 | 0,20 |
|---|---|---|---|---|
| Rampa con el piso (el `base_adapter` de hoy) | 0 / 146 | 0 / 29 | 0 / 59 | 0 / 153 |
| Corte en seco con el 0 | 0 / 10 | 0 / 181 | 0 / 70 | 0 / 157 |
| Contragolpe 1 rps 0,15 s | 0 / 184 | 2 / 194 | 23 / 63 | 5 / 179 |
| Contragolpe 2 rps 0,15 s | **81** / 103 | 65 / 70 | 52 / 124 | 26 / 28 |

- **Rodado aparte en arcos** (`park_fixed_roll_arc` > 0, nuevo): mide por separado lo que rueda en los arcos y en las
  rectas.
  - Con el contragolpe de 2 rps, rectas 0,13 y arcos 0,04: **97/200**, pero con 73 roces.
  - Con rectas 0,13 y arcos 0,07 / 0,10: 69 / 94.
  - Con rectas 0,10: 8–23.
  - Con corte en seco: 0 en todos.
  - Con el contragolpe de 1 rps: 0.
- **Más margen, o empezar en otro sitio**, lo empeora: `park_fixed_margin` 0,02 / 0,03 dan 0 / 0 (no queda sitio para
  enderezar), y `park_fixed_ahead` 0,13 / 0,16 con 0,65 / 0,76 rad dan 0.
- **Por defecto (0,06 m/s, sin piso) no cambia:** con `park_fixed_roll_arc` 0, un solo rodado, 195/200. Medirlo aparte
  bajaba a 164.

**Conclusión:**
- **A ~0,3 m/s el aparcamiento fijo no es fiable en el lab.**
  - Con una parada normal, 0/200. Aunque se corte en seco, el coche rueda 13 cm en un lote con 11,7 cm de holgura.
  - Solo con el contragolpe de 2 rps llega a 81–97/200, con roces en un tercio de las rondas. Y ese contragolpe el lab
    lo sobrevalora en recto.
- **No se porta a robotek-learn** como opción de coche.
- Lo que haría falta en el coche:
  - más fuerza a baja velocidad (engranajes 30:54), o
  - una frenada que pare en ≤3–4 cm desde 0,3 m/s.

## El lote desde el LiDAR (`park_fixed_sense: 1`, 9 nov)

En el coche (8 nov, 23:25–23:43) la pared exterior salía en el escaneo a y −1,52…−1,57 en vez de −1,50, y un límite a
~3 cm de donde lo pone la v3. La pose del mapa coloca el lote mal por esa cantidad, y el lote solo tiene ~2,6 cm de
holgura por lado.

**Qué hace** (`park_fixed.py`, opcional, por defecto apagado). Con cada escaneo:
- **Pared exterior:** ajusta una recta a sus retornos junto al lote, en una banda de ±10 cm de donde se espera, sin
  contar los de los límites. Su distancia corrige y (contra la pared) y su pendiente corrige el rumbo, girando alrededor
  del lote.
- **Placas de los límites:** usa los retornos a ±6 cm de su x esperada y dentro del fondo del lote, contra la cara que
  da al LiDAR. Corrigen x.
- **Filtro:** la corrección se suaviza (0,3 del error por escaneo) y se acota a ±12 cm / ±8°.
- **Si no ve nada**, mantiene la última corrección.
- **Zona muerta:** cada parte solo se aplica si pasa de 8 mm / 0,75°.

**Lab** (`real_v3`, solo aparcar, capas 0–49 × 2 × semillas 0–1). `obstacle_lab_suite.py --field-shift=DX,DY` mueve la
pared exterior de abajo DY, y el lote (DX, DY), en el marco del mundo:

| Campo | Apagado | Toda la corrección | **Con zona muerta (por defecto al encenderlo)** |
|---|---|---|---|
| Reglamento | **195** | 157 | **188** |
| Pared y lote +3 cm / −6 cm | 0 | 127 | 85 |
| −3 cm / −6 cm | 0 | 82 | 45 |
| +3 cm / −2 cm | 0 | 128 | 112 |
| 0 / +4 cm | 0 | 90 | 143 |

- **Sin la corrección, 2–6 cm de error del campo bastan para no aparcar nunca** (0/200).
- Con ella aparca 45–143/200, según el campo.
- En el campo del reglamento pierde un poco: 188 frente a 195, por el ruido de la estimación. Sin zona muerta, 157.
- **Piso de 0,25 m/s y contragolpe de 2 rps** (corrección sin zona muerta): 5/200 en el campo del reglamento y 3/200 en
  el desplazado, frente a 97/0 sin ella. A esa velocidad no ayuda.
- **Pruebas:**
  - `test_sense_finds_a_shifted_wall_and_lot`: una pared 5 cm más fuera y un lote 3 cm más allá dan la corrección que
    los devuelve a su sitio;
  - con `park_fixed_sense: 0`, la pose del mapa no cambia.

## El campo del coche: lote a `park_lot_end` 0,31, pared que deriva, arranque (9 nov)

Datos del coche (8 nov, noche):
- el LiDAR ve el límite a 17 cm del reglamento: `park_lot_end` 0,31;
- la pared exterior sale a y −1,52…−1,59 y cambia de una ronda a otra;
- con todo el giro hace falta el arranque de 2 rps durante 0,2 s.

**El lab ahora** (`eea345a`, opciones apagadas por defecto):
- `--field-shift=-0.17,DY` pone el lote donde está en el campo del coche y aparta la pared DY;
- `kick_speed` / `kick_s` / `kick_after`: el arranque de `base_adapter`;
- `lock_breakaway`: parado con todo el giro, el coche no arranca con menos de esa velocidad pedida (0,3 ≈ 1,3 rps).

**Pasada rápida:** capas 0–9 × 2, semilla 0, 20 rondas, con `park_lot_end` 0,31. Cada celda es «sin `park_fixed_sense` /
con `park_fixed_sense` 1». El remoto dio los mismos números.

| Coche | Pared en su sitio | Pared 4 cm más afuera |
|---|---|---|
| Despacio (0,06 m/s, `real_v3`) | 20 / 19 | 3 / **16** |
| Como hoy: piso 0,25 m/s, contragolpe 2 rps, arranque 2 rps, `lock_breakaway` 0,3 (rodado 0,13 / 0,04) | 1 / 0 | 0 / 0 |

**Piso más bajo tras el arranque** (con `park_fixed_sense` 1, pared en su sitio):

| Piso | Rondas | Rodado 0,04 | Rodado 0,08 |
|---|---|---|---|
| 0,10 m/s | 20 | 0 | 0 |
| 0,12 m/s | 50 | — | 0 |
| **0,14 m/s** (≈ 0,62 rps) | 20 / 50 | 15/20 | **18/20; 42/50** |
| 0,16 m/s | 50 | — | 5 (38 con roces) |
| 0,18 m/s | 20 | 1 | 1 |

- **La corrección del LiDAR resuelve la deriva de la pared** cuando el coche va despacio: de 3 a 16 de 20.
- **A la velocidad de hoy no aparca, con corrección o sin ella.**
- **Con el arranque y un piso de 0,14 m/s aparca 42/50, pero el margen es muy estrecho:**
  - 0,12 m/s da 0: el arco de entrada se corta pronto y la bajada recta lo deja poco hondo;
  - 0,16 m/s, 5.
  - En el coche la velocidad real varía ±20 %. Si se prueba, empezar con `motor_min_rps:=0.62` y ver en la bolsa la
    velocidad real de cada paso.
  - En el coche, 0,62 rps continuos con todo el giro aún no se han probado. Con pulsos de 0,66 rps se paraba.

## Lote del coche medido (0,3675 m, 10 nov 2026)

El coche real mide 24,5 cm, y el lote pasa a 1,5 × 0,245 = 0,3675 m (`vehicle.RULES_LENGTH`, commit `6108f17`). Para
comparar se corrió en el remoto el código de antes de ese commit (lote de 0,3495 m) frente al actual: `real_v3`, solo
aparcar (`park_after=0`), capas 0–49 × 2 sentidos × semillas 0–1, 200 rondas.

| | Lote de 0,3495 m | Lote de 0,3675 m |
|---|---|---|
| Fijo (`park_mode=1`) | 195 (5 tocan un límite) | **197** (3) |
| Planificador (`park_mode=0`) | 35 (60 tocan, 105 torcidos o fuera) | **173** (27 tocan) |

- El fijo apenas cambia: arranca desde el límite lejano (`park_lot_end`), y 1,8 cm más de lote por detrás le dan
  algo más de margen.
- El planificador mejora mucho: con el coche de `real_v3`, que gira ~11 % más cerrado que su plan, el lote de 0,3495 m
  no le dejaba margen.
- **Fallo del lab corregido:** `obstacle_lab_suite.py` guarda los campos en `/tmp/obstacle-lab-fields` y reutiliza
  los que ya existen. La primera pasada usó campos del lote viejo con el código nuevo (fijo 87, planificador 49, la
  mayoría tocando un límite). Ahora el largo del lote va en el nombre del campo (`reg0-ccw-park0.3675`).
- **Pendiente:** rondas completas (vueltas y aparcamiento), y el campo del coche (`park_lot_end` 0,31) con el lote
  nuevo.
