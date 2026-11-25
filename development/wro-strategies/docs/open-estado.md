# Open: estado actual

Página corta para retomar el trabajo. **Se reescribe, no se le añaden secciones.** La historia y el
detalle están en los documentos enlazados al final.

Actualizado: 12 nov 2026 (v5 simplificado con el lab realista).

**12 nov 2026:** el v5 se simplificó probando en las 16 islas de las reglas (`--suite centres`) con el coche
`real_v4` y los huecos del LiDAR medidos. Salen 8 parámetros o constantes y entra la estima de la pared de enfrente
entre escaneos. Con huecos: 79 % de rondas sin choque, frente al 46 % del código del 11 nov; sin huecos, 100 %.
Detalle y tablas: [open-simplificacion-20261112.md](open-simplificacion-20261112.md).
Después se arregló el driver del LD19 (robotek-learn `5efc074`): consultaba los escaneos a 10 Hz y el LiDAR gira a
9,9 Hz, así que perdía vueltas enteras. Con la consulta a 200 Hz el Pi midió 0 huecos en 60 s, con el coche quieto y
también con 3 de sus 4 núcleos ocupados. Antes eran 0,15 por segundo quieto y 0,33–0,68 por segundo en marcha. Falta
confirmarlo con una ronda en marcha; si se confirma, en el coche vale el resultado del lab sin huecos (100 %).

## Estrategia

- **v5**, la única desde `ba5f7c2` (los v1–v4 se borraron), también en el coche real.
  - Código: `src/robotek_open/robotek_open/v5/` (`mission.py`, `scene.py`, `node.py`, `settings.py`,
    `recording.py`), 590 líneas.
  - Perfil: `src/robotek_open/config/open_v5.yaml`.
- **En el coche real** (3 nov 2026): corre desde robotek-learn (`src/robotek_open`, copia del v5 con los valores del
  coche), con `ros2 launch robotek_course car.launch.py strategy:=robotek_open executable:=open_v5`. Ese launch tiene la
  calibración actual: dirección medida el 1 nov, ±19° simétricos, y el motor 310 en M1. `robot.launch.py` de este repo
  todavía tiene la dirección vieja y el TB6612: no usarlo en el coche. Un cambio del v5 aquí hay que copiarlo allí.
  Falta medir la velocidad del motor nuevo.
- **Mapa del código:** `python3 tools/code_map.py src/robotek_open/robotek_open/v5/*.py`.
- **Parámetros:** la clase `Params` de `v5/mission.py` (p. ej. `cruise_speed`, `corner_speed`, `inner_gap`,
  `turn_front_distance`, `corner_lookahead`, `turn_tolerance`, `lateral_kp`, `brake_margin`).
- **Coche real** (robotek-learn, 11–12 nov): `bash tools/car-run.sh open`, valores en `config/car_picam.yaml`
  (crucero 0,85, curvas 0,64) y detector de choques (`detect_crash`).

- **Curso y guía** (12 nov 2026): la estrategia de referencia del curso (`my_open`, rama `solutions` y etiquetas
  `step-0` a `step-9` de robotek-learn) y toda la guía del Open en Portfolio-Astro siguen ahora esta v5
  simplificada: giro a tope hasta 0,3 rad, distancia por la pared de frente, una velocidad de esquina con frenada
  antes de cada una y corrección del rumbo con la pared de la isla. En su lab (coche `real_car_v1`): 36/36 válidas,
  41,85 s; Gazebo 35,56 s (ccw) y 35,53 s (cw), 30 puntos. Punto frágil medido: la parada (motor al 115 %: 29/36;
  con `CORNER_SPEED` 0,9, 36/36). Detalle en `course/maintainers/tuning/RESULTS.md` de robotek-learn.

## Números de referencia

| Prueba | Resultado | Coche |
|---|---|---|
| Lab, set estándar de 12 (`open_lab`) | **12/12** válidas, 40,73 s de media | corregido (`2b17266`) |
| Gazebo, set estándar `std12-v5-e-*` (sin ventana, ×2) | 12/12 válidas, margen mínimo 9,4 cm | anterior (21 oct) |
| Gazebo con ventana, `square100` | CCW 33,197 s, CW 32,897 s, 30 pts, válidas | anterior (21 oct) |
| Ronda de humo de hoy (`model20261026-v5only-smoke-sq100-ccw`) | 30 pts, válida, 32,7 s | corregido |
| Mejor ronda con GUI registrada | 29,312 s, de otro perfil y otra estrategia (8 oct) | anterior |

- La mejor ronda del 8 oct no se puede comparar con el v5: la midieron otra estrategia y otro coche.
  Ver [best-realcar-open-round.md](open-challenge-runs/best-realcar-open-round.md).
- **Pendiente:** el set estándar de Gazebo con el coche corregido. El último es del 21 oct.

## Perfiles del coche en el lab

`open_lab --car <perfil>`; `--car-param nombre=valor` cambia un valor del perfil y `--spawn x,y` la salida. Con
`real_v2` el lab corre por defecto solo el campo clásico (`--suite classic`: `square100`, CCW y CW, menos de 1 s); el
set estándar de 12 queda como prueba de regresión del perfil por defecto.

| Perfil | Archivo | Qué es | Para qué |
|---|---|---|---|
| `real_v1` (por defecto) | `robotek_evaluation/config/real_car_v1.yaml` | El coche de Gazebo `real_car:=true`, medido el 8 oct con el motor viejo: 1,28 m/s mandados → 0,60 m/s, wheelbase 0,13 del modelo, servo con el retraso del plugin, tres copias de cada escaneo | Comparar estrategias y comprobar contra Gazebo. Set estándar: 12/12, 40,73 s |
| `real_v2` | `robotek_evaluation/config/real_car_v2.yaml` | El coche real del 4 nov (pruebas 5–13): `motor_type: 2` y tope de 2,5 rps (0,521 m/s mandados → 0,55 m/s reales; 4 rps → 0,76, 6 rps → 0,75), arranque lento (0,3 s + 0,4 s), wheelbase real 0,119 y giro máximo efectivo de 19,1° (radio 0,34 m; identificado con el servo y el giroscopio de las pruebas 11 y 13: 1,71–1,98 rad/s a 0,57–0,70 m/s), servo con 10/50/90 % a 0,12/0,20/0,29 s, un escaneo por stamp y el **bucle de control a 38,8 Hz** | Predecir lo que hará el coche real antes de probarlo. `measured_dt` (por defecto `true`) es el nodo arreglado en `9ce7d67`; `--car-param measured_dt=false` reproduce el nodo de las pruebas. Parada opcional del motor con todo el giro (`stall_steer`) |
| `real_v3` | `robotek_evaluation/config/real_car_v3.yaml` | El coche real desde el 8 nov: motor en M2 sin tipo (la placa controla la velocidad), engranajes 54:30, 4,4 rps por m/s, un 0 normal lo para (sin resets). Motor: 0,10 s + 0,30 s de retraso y 1,0 m/s² (ajustado a los pulsos del 8 nov), rampa de `base_adapter` 1,0 / 0,6 m/s², tope 6,7 rps. Servo: tope en 1793 µs (0,307 rad), giro efectivo ×1,114 con subviraje 0,10 (radio 0,335 m a 0,2 m/s, 2,28 rad/s a 0,8 m/s), tiempos reajustados a las pruebas 11/13 y a la ronda 2 del Obstacle del 4 nov. Fallo opcional «todo el giro y no gira» (`no_turn_lock`, apagado) | El coche de ahora. Campo clásico con los ajustes del coche: 2/2, 12 giros, 23,5 s (real 26,7 s: el lab recorre 18,5 m y el coche ~23 m, ver el yaml). Con tope de 0,6 m/s el lab choca en la esquina 1 y el coche real terminó (`steer_gain=1.0` sí termina). Con `no_turn_lock=7` choca a ~13 s, como la ronda 3 del 8 nov |

- **Causa del choque con la isla (pruebas 9, 11 y 13).** Hasta `9ce7d67`, el nodo del v5 integraba el giroscopio con un
  `dt` fijo de 1/50 s, pero en el Pi su temporizador iba a 38,8 Hz (prueba 11), 38,6 Hz (prueba 9) y 37,9 Hz (prueba 13). Lo dice `/open/steer` en los bags; en la
  prueba 6 iba a 48,6 Hz. En la curva 1 de la prueba 11, el giroscopio suma ~118° y las paredes del LiDAR ~121°, pero el
  yaw del v5 marca 91°: el coche salió de la curva apuntando ~30° hacia la isla. El radio real es de 0,33–0,35 m
  (0,41 m en `real_v1`), no de 0,25 m: esa cifra de las notas daba por hecho 0,45 m/s.
- `real_v2` con el nodo viejo (`measured_dt=false`) lo reproduce. Con `inner_gap` 0,35, desde la salida de la prueba 11
  (`--spawn 0.30,-0.98`, `square100` CW), choca con la isla nada más acabar la curva 1: 1 giro, 3,9 s. Con
  `turn_delay_distance` 0,15 choca igual, ~1 s más tarde (4,7 s). Es lo que pasó en la prueba 13 (choque tras la curva 1 a
  los ~4,9 s; bucle a 37,9 Hz, ~33° de más según las paredes). En el campo clásico, 0/2 en los dos casos (y 0/12 en el
  set estándar).
- **Con el nodo arreglado** (por defecto), en el campo clásico las dos rondas hacen los 12 giros sin tocar nada. El margen
  mínimo es de 10 cm con `turn_delay_distance` 0 (33,0 s) y de 24 cm con 0,15 (36,8 s). A 48,6 Hz con el nodo viejo, el
  error (~2,5° por curva) se acumula: es lo que pasó en la prueba 6, que se atascó en la curva 8.
- Aun sin choques, `real_v2` no da rondas válidas: tras DONE el coche sigue rodando (deceleración de 0,6 m/s² y el
  retraso del motor), así que no cuenta la parada. En la prueba 6 el coche real también siguió ~1 m después de mandar 0.
- Límites: el campo es el del set estándar, no la pista de prácticas, y la curva de velocidad solo tiene 4 puntos.
  Tampoco modela el freno de pared de `base_adapter`, el deslizamiento ni la carga variable del Pi (el bucle va a un
  ritmo fijo).

- `real_v4` (`real_car_v4.yaml`): el coche desde el 11 nov (motor nuevo): `steer_gain` 1,0, subviraje 0,35, velocidad
  0,93 × la pedida y huecos del LiDAR opcionales (`--car-param scan_gap_rate=0.68`). Con `--suite centres` (las 16 islas
  × 2 sentidos) es la prueba de referencia del coche ([open-simplificacion-20261112.md](open-simplificacion-20261112.md)).

## Cómo medir

**Un cambio del Open se mide con las 16 islas y 9 salidas por ronda**, no desde una sola salida (12 nov 2026: dos
regresiones pasaron desapercibidas así):
`python3 -m robotek_evaluation.open_lab --suite centres --starts grid --car real_v4 --car-param gyro_scale=0.94 --param=...`
(valores del coche en `car_picam.yaml` de robotek-learn; referencia 864/864 con 3 semillas).

```bash
tools/remote.sh sync
tools/remote.sh run 'export PYTHONPATH=$(ls -d src/*/ | tr "\n" ":")$PYTHONPATH; python3 -m robotek_evaluation.open_lab --brief --against /tmp/open-base.json --param inner_gap=0.20'
tools/remote.sh run tools/open_suite_quiet.sh <tag>          # set estándar de Gazebo, 12 rondas
tools/remote.sh fetch && python3 tools/round_digest.py <ronda> [--at fault]
```

- **Lab:** `--out` guarda una línea base y `--brief --against` muestra solo lo que cambia. Es
  determinista: cambia solo si cambian el código o el coche.
- **Perfiles:** compararlos solo con el set estándar (`open_standard_suite.sh` u `open_suite_quiet.sh`).
  Las finales se validan con GUI en el Mac.
- **El runner** termina con una línea JSON corta. El resultado completo está en `summary.json` y
  `round.json`; leerlo con `round_digest.py`, no entero.

## Historia y detalle

- [open-reimpl-v5.md](open-reimpl-v5.md): diseño del v5, resultados del lab y de Gazebo y lo que falló.
- [open-lab.md](open-lab.md): qué modela el laboratorio y su fidelidad.
- [open-challenge-runs/](open-challenge-runs/): las mejores rondas, la historia y las validaciones por
  contexto.
- [next-steps.md](next-steps.md): el estado general del proyecto.
