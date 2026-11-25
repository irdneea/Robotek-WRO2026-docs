# Obstacle v2: qué queda para cerrar la fase 4 y pasar a la 5

Estado al 25 de octubre de 2026. Este documento es la lista de trabajo; el plan completo está en
[obstacle-reimpl-plan.md](obstacle-reimpl-plan.md) y los resultados en
[obstacle-reimpl-v2.md](obstacle-reimpl-v2.md) (la iteración del 25 oct está en
[su propia sección](obstacle-reimpl-v2.md#iteración-del-25-oct-2026-bucle-rápido-memoria-de-color-líneas-de-esquina-y-salida)).

## Dónde estamos

- **Bucle de iteración:** `python3 tools/obstacle_lab_suite.py --seeds 0-4 --early` corre las 50
  rondas en ~26 s desde `src`. Para no sobreajustar, usar también `--layouts 5-24`.
- **Implementado:** en `src/robotek_obstacle/robotek_obstacle/v2/` (`mission.py`, `corner.py`,
  `scene.py`, `settings.py`):
  - memoria de señales por asiento;
  - plan lateral con rampas;
  - líneas recta-arco-recta por esquina;
  - desvío para ver de antemano las señales interiores a la salida de esquina;
  - retroceso de salida.
- **Laboratorio:** **29/50 válidas** (línea base 15/50).
  - Pasan los 5 campos CCW (`reg2-ccw` 4/5) y `reg1-cw`.
  - Fallan `reg0-cw`, `reg2-cw`, `reg3-cw` y `reg4-cw`.
- **Set reservado** (layouts 5–14, semilla 0): **7/20**.
- **Tamaño:** 513 líneas / 185 de complejidad / máximo 10 por función. **Supera** el objetivo de
  360/110.
- **Pruebas:** **102 pasan**.
- **Sin push.** Commits de esta iteración: `f7dc73a`, `a7ffcfd`, `54f97d2`, `ffbb3b1`, `8bf905f`.

## Estado al 25 oct 2026 (tarde)

- Nodo `obstacle_strategy_v2`, perfil `obstacle_v2.yaml`, `--strategy v2` y `--layout regulation-park` en el
  runner (`b0137a9`). Gazebo `reg4-ccw`: 40 puntos, válida, 115,6 s; con aparcamiento 37 (no aparcó en 180 s: la
  búsqueda de correcciones bloquea el bucle). En el curso, `my_obstacle` (el mismo v2) hizo 47/55 en Gazebo.
- Laboratorio: 88/100 sin aparcamiento (layouts 0–49 × 2), 11/20 con 55 puntos con aparcamiento (layouts 0–9 × 2).
- Guía publicada en local: robotek-learn (`266fc71`, rama `solutions-obstacle`, etiquetas `obstacle-step-0..9`)
  y Portfolio-Astro (`c00b983`, `/learn/obstacle-strategy`). Sin push. Especificación: [obstacle-guide-spec.md](obstacle-guide-spec.md).
- Próximo: aparcamiento sin bloquear el bucle (hilo o búsqueda acotada por nodos) y más rápido; la esquina verde
  interior → roja exterior (3,4 cm ideal); set estándar en Gazebo con ventana.

## Iteración del 26 oct 2026: máquina remota, capacidad de Gazebo y hallazgos

Todo se corrió en la máquina remota ([maquina-remota.md](maquina-remota.md)).

**Refactor sin cambio de comportamiento.**
- Todas las funciones del v2 quedan en complejidad ≤ 10 (`4816c5a`). Antes: `corner.plan` 15, `_corner` 15,
  `park._plan` 15, `node.control` 17 y `_look` 13.
- `_planned` busca sus nudos con `bisect`, O(log n) (`6d82a33`).
- Verificación: el laboratorio da los mismos resultados ronda a ronda, solo cambia la CPU. Son 120 rondas:
  layouts 0–49 × 2 sentidos (88/100) y aparcamiento 0–9 (11/20). `bisect` además coincide con el barrido
  en 20 000 perfiles aleatorios.

**Capacidad de Gazebo en la remota** (Ryzen 9 7900X, RTX 4080 Super, WSL2) con
`tools/obstacle_gazebo_batch.py`, v2 a 1x y render en la GPU (`--gpu`, Mesa d3d12):

| Rondas a la vez | Resultado frente a la referencia | Puerta de calidad | Velocidad |
|---|---|---|---|
| 1 | 4/4 válidas, 40 pts | 4/4 | 0,89–0,92 |
| **2** | **idénticos** (±0,1 s) | 2/2 | 0,89–0,90 |
| 4 | mismos puntos, un margen pasa a «tight» | 3/4 | 0,85–0,89 |
| 6 | una ronda rota (0 pts), márgenes peores | 3/6 | 0,79–0,84 |
| 8 | carga 69 en 24 núcleos (se cortó) | — | — |

- El límite es la **CPU**: cada ronda son 8 procesos ROS. La GPU no pasa del 20 %.
- **Usar 2 rondas a la vez.**
- A máxima velocidad (`--real-time-factor 0`) una ronda llega a 1,3x con render por CPU y a 1,5x con GPU,
  y no pasa la puerta de calidad. 3x no es alcanzable.
- Hallazgo de banco: `gz sim -s` sobrevive al SIGINT del runner. Sin `clean_sim.sh` entre rondas, el
  servidor viejo se mezcla con la ronda siguiente y la rompe (`inf` en el JSON, «Missing measured
  steering»). El lote mata lo que queda en la partición de cada trabajo.

**Línea base con el coche corregido** (`2b17266`: ejes y vía del STEP, batalla 118,83 mm): **89/100** en
layouts 0–49 × 2 sentidos y **8/20** con aparcamiento (layouts 0–9). Los experimentos de abajo se midieron
contra la línea base anterior (88/100) con una geometría intermedia (`790ca48`); quedaron por debajo de
ambas, así que la conclusión no cambia, pero hay que repetirlos con este coche antes de reutilizar sus
números.

**Hallazgos de estrategia (todos revertidos; ninguno mejoró).**

| Cambio | Laboratorio 0–49 × 2 | Qué pasó |
|---|---:|---|
| Línea base | 88/100 | — |
| Referencia por el punto más cercano de la línea planificada, no por la normal del carril | 84/100 | arregla `reg1-ccw` y `reg38-cw`; rompe 6 CW contra el muro exterior |
| 0,12 m/s en las esquinas con < 6 cm de margen planificado | 85/100 | arregla `reg1-ccw`; rompe 4 |
| Aparcar a 0,08 / 0,10 m/s | 0/20 y 0/20 (aparcamiento 0–9; era 11/20) | toca los límites del aparcamiento |
| `COAST` proporcional a la velocidad (a 0,06 m/s es el mismo valor salvo 10⁻¹⁸ m) | 7/20 | **el aparcamiento es caótico** |

- **Esquinas S** (señal interior verde → exterior roja, en el marco espejado):
  - Es el peor caso sobre el papel: 3,4 cm, y su espejo 4,0 cm.
  - El seguidor corta la curva hacia dentro: el feed-forward mira 0,1 m adelante y gira antes que el
    arco. Después sale con ~45° de los 90° y llega a 5,8 cm de error (`reg0-cw`).
  - Cambiar el control o la velocidad mueve fallos de un campo a otro: el set está sobreajustado.
- **El aparcamiento no es robusto.**
  - Un cambio de 10⁻¹⁸ m mueve 4 de 20 rondas; el 11/20 actual es suerte.
  - En Gazebo, `v2-park-smoke-reg4-ccw` muestra por qué:
    - La localización durante la maniobra es buena (~3 mm).
    - La ejecución del plan nominal diverge: la guarda corta un movimiento a 40° dentro del aparcamiento.
    - Las correcciones dan vueltas entre 35° y 49°.
    - Una búsqueda de 41 262 nodos bloquea el bucle ~10 s, y la ronda llega a los 180 s.
- **Siguiente:** un aparcamiento de lazo cerrado, sin A* durante la ronda.
  - Una maniobra fija para la geometría del reglamento (el aparcamiento siempre es el mismo).
  - Cada movimiento termina por rumbo (giroscopio) o por distancia al muro o al límite (LiDAR), con
    márgenes que toleren ±1 cm.
  - Medirlo con varias semillas y con perturbaciones: un resultado que cambia con 10⁻¹⁸ m no sirve para
    decidir.

## Iteración del 26 oct 2026 (noche): Gazebo con el coche nuevo, lab más rápido y oclusión

**El URDF de las rondas de Gazebo.** El más reciente es el de `2b17266`, y el Mac y la remota lo tienen en
`src` e `install`. Pero `digest-test-reg4-ccw` (115,6 s) corrió con el URDF de `8caa571` y el `vehicle.py` de
`790ca48`, y `v2-park-smoke-reg4-ccw` con el de `0a23cbe`, según su `source_sha256`. La remota además no
compilaba `robotek_open` (su `build/` apuntaba al `open_realcar_v4.yaml` borrado); se limpió esa caché.

**Set estándar en Gazebo con `2b17266`** (`v2-car2b17266`, 2 a la vez, 1x, GPU): **8/10** válidas con 40 pts.

| Campo | Gazebo | Lab (semilla 0) |
|---|---|---|
| reg0-ccw | 40, 99,2 s (no pasa la puerta de calidad) | 40, 98,8 s |
| reg0-cw | 1, contacto a 8 s | 1, contacto `sign_green_1` a 7,3 s |
| reg1-ccw / reg1-cw | 40, 95,4 s / 40, 109,1 s | 40, 94,9 s / 40, 110,8 s |
| reg2-ccw / reg2-cw | 40, 106,5 s / 40, 114,9 s | **6 y 3: contacto** |
| reg3-ccw | 40, 106,0 s (tight) | 40, 105,3 s |
| reg3-cw | **4: lado incorrecto en `sign_red_1` a 21,3 s** | 40, 119,0 s |
| reg4-ccw / reg4-cw | 40, 115,6 s / 40, 99,4 s | 40, 115,4 s / 40, 98,9 s |

Coinciden 7 de 10 campos, y en los válidos el tiempo difiere ≤ 0,6 s.

**Perfil del lab.** Una ronda (`reg4-ccw`) costaba 16,8 s de CPU, y **9,2 s eran `lidar_odometry._align`**,
la odometría del coche: un vecino más cercano por fuerza bruta que sumaba un array `(n, m, 2)` sobre el eje
de 2. Escrito como `dx² + dy²` da los mismos bits (3000 casos aleatorios) y es 5,6× más rápido (`d664ca5`).
Las 120 rondas del lab salen idénticas campo a campo, también el aparcamiento. Una ronda baja a 9,6 s, y
100 rondas de 79 a 49 s. La misma función corre en el coche real. Lo que queda del simulador (márgenes del
contorno ~2 s, juez ~1,5 s, rayos 0,5 s) no justifica vectorizar más. La GPU no ayuda al lab: los rayos son
pocos y la estrategia es Python con ramas.

**Oclusión de la cámara en el lab** (`a9c5bbb`). Antes el lab daba el color de todo pilar en el campo de
visión, aunque lo tapase otro.
- Ahora muestrea la cara del pilar y lanza rayos 3D desde la cámara (14,2 cm de alto, `REAL_CAMERA_HEIGHT`).
  Los pilares miden 10 cm y los muros 11 cm: la cámara ve por encima, y un pilar lejano asoma tras uno cercano.
- La parte visible debe pasar el filtro de `color_blocks`: ≥ 30 px², ≥ 8 px de alto y 1,05 veces más alto
  que ancho. Un pilar que solo asoma la punta no cuenta.
- Oculta ~10 % de las vistas (`reg3-cw`: 52 de 466), pero ninguna de las 100 rondas cambia de puntos ni de
  validez (89/100). Con aparcamiento cambian 7 de 20 en los dos sentidos (8 → 9/20): es el caos del
  aparcamiento, no una mejora.
- No explica las diferencias con Gazebo. `--no-occlusion` da el lab anterior bit a bit.

## Iteración del 26 oct 2026 (noche, 2): aparcamiento de lazo cerrado

**Diseño** ([park.py](../src/robotek_obstacle/robotek_obstacle/v2/park.py), `a9f7791`). El plan nominal
(A* sobre arcos de 3 cm) se sigue calculando **una vez antes de la ronda**. Durante la ronda no hay búsqueda.
- Cada movimiento termina en un **objetivo absoluto** del plan: un arco en su rumbo final (giroscopio), una
  recta empinada en su profundidad (LiDAR: distancia al muro), otra recta en su punto a lo largo.
- Antes del plan, una recta hasta la x de la pose de plan (la aproximación se pasaba ~2,5 cm).
- Si el coche llega sin alinear, retrocede 0,5 m por la línea y vuelve a aproximarse (como mucho 2 veces).
- Tras cada parada mide cuánto rodó (media móvil) y, si se quedó corto del objetivo, sigue. En el lab el
  coche no rueda los 12 mm de `COAST` y cada movimiento se quedaba corto.
- Después del plan: enderezar (marcha alterna a tope hacia paralelo, hasta 12 movimientos o dos seguidos de
  menos de 5 mm) y centrar en x.
- Guarda de 12 mm (8 mm daba más toques; 16 mm, menos aparcamientos).

**Modelo cinemático primero** (en `/tmp`, fuera del repo): ejecutar el plan con errores de servo,
localización e inercia. Con longitudes relativas (como antes, sin A*) aparcaba 165/300; con objetivos
absolutos, 250/300; con la profundidad por LiDAR y el enderezado, 277/300.

**Lab, layouts 0–9 × 2 sentidos × semillas 0–4 (100 rondas):**

| | A* (antes) | Lazo cerrado |
|---|---:|---:|
| Válidas (55 pts) | 29 | **57** |
| Aparcado parcial (47) | 14 | 8 |
| Sin aparcar a tiempo (37) | 29 | **0** |
| Toca un límite (37) | 5 | 6 (todos CW) |
| Puntos de media | 35,5 | **39,7** |

Las 27 rondas restantes fallan en las vueltas. El lab sin aparcamiento queda idéntico (100/100 rondas).

**Gazebo** (`v2-park-closed`, 2 a la vez, 1x, GPU): `reg1-ccw` y `reg4-ccw` **55 pts válidas** (139,9 y
151,5 s), la primera vez que el v2 aparca en Gazebo. `reg4-cw` toca `parking_limit_a` al aparcar (40 pts).
`reg1-cw` empuja `sign_red_2` fuera de su círculo en la primera vuelta (18 pts).

**Hallazgo: en CW la x se pierde junto al hueco.** En `7:cw:0` la x estimada se queda quieta (y retrocede
1 cm) mientras el coche avanza 6,5 cm hacia el límite delantero. En CCW el error de pose al aparcar es
< 1 cm; en CW tiene picos de 2,6–4,9 cm.
- Poner las placas de los límites en el ajuste del localizador: 55/100 (sin cambio), revertido.
- Congelar x durante el aparcamiento: 0/100 y 51 toques; la odometría sola no basta.
- Hipótesis: en CW el hueco queda al principio de la recta y la esquina cercana queda detrás, fuera del
  campo del LiDAR (±110°); en CCW está delante, a 1,2 m.

## Iteración del 26 oct 2026 (noche, 3): la x en CW al aparcar

**Diagnóstico.** En CW, con el coche dentro del hueco, el escaneo tiene unos 70 puntos, todos entre 57° y
110° de rumbo:
- la placa delantera tapa el frente (a ~2 cm del LiDAR, bajo su alcance mínimo de 16 cm);
- el muro exterior está a ~11 cm, también bajo el mínimo;
- solo queda la cara inferior de la isla, que fija y. La x la fija la esquina de la isla: en CCW se ve a
  85°, en CW a ~110°, el borde del campo del LiDAR.

El coste del ajuste por muros es casi plano en x entre −4 y +8 cm, así que x depende de la odometría. Y la
odometría fallaba por dos motivos:
1. **Las ruedas no giraban paradas.** La estrategia manda un `Twist` (v, ω); con v = 0 el ángulo no se puede
   codificar y tanto `mapping.py` del coche real como el lab conservan el anterior. En `PARK_STEER` el servo
   no se movía: giraba durante el movimiento, y medio arco iba con otra curvatura.
2. **Distancia y signo.** La odometría LiDAR con casi solo líneas paralelas a x da mal el avance. Además, la
   inercia tras parar en marcha atrás se sumaba hacia delante (con la velocidad mandada a 0 el signo es +).

**Arreglo** (`a1ec699`):
- En `PARK_STEER` se manda 3 mm/s en la marcha del movimiento siguiente. Es más de 1 mm/s (lo que hace falta
  para que el `Twist` lleve el ángulo) y menos que los 5 mm/s de banda muerta del motor: el servo gira y el
  coche no se mueve. El aparcamiento anterior hacía algo parecido (`CREEP`).
- En los arcos a tope o a media dirección, la distancia sale del giroscopio: |Δrumbo| × batalla /
  tan(dirección), con el signo de la marcha del movimiento, también mientras rueda tras parar.

**Lab** (layouts 0–9 × 2 × semillas 0–4):

| Variante | Válidas | Toques |
|---|---:|---:|
| Lazo cerrado (`a9f7791`) | 57 | 6 |
| + distancia por giroscopio | 63 | 3 |
| + servo con el coche parado (`a1ec699`) | **70** | **2** |
| Igual, sin distancia por giroscopio | 59 | 14 |

Probado y descartado:
- placas de los límites en el ajuste del localizador: sin cambio, porque sus puntos están bajo el alcance
  mínimo;
- congelar x en todo el aparcamiento: 0–15 válidas;
- no corregir con el coche parado: 11 válidas.

El lab sin aparcamiento queda idéntico.

**Gazebo** (`v2-park-creep`, 2 a la vez, 1x, GPU): 55 pts válidas en `reg0-ccw` (130,8 s, no pasa la puerta de
calidad), `reg1-ccw` (131,7 s), `reg4-ccw` (151,8 s) y **`reg4-cw` (133,5 s), que antes tocaba el límite**.
`reg1-cw` y `reg2-cw` empujan un pilar en las vueltas.

## Iteración del 26 oct 2026 (noche, 4): pilares empujados en CW con aparcamiento

**Reproducción.** El lab repite los dos fallos de Gazebo en las 5 semillas: `reg1-cw` toca `sign_red_2` a
73,5 s (Gazebo 74,4 s) y `reg2-cw` toca `sign_red_1` a ~25 s (Gazebo 27,2 s). Es geométrico, no ruido.

**Layout.** Con aparcamiento, el generador mueve los pilares del tramo de salida a la fila interior (0,4 m
del muro interior), como manda el reglamento (aleatorización, paso 5). En `reg1-cw`, `sign_red_2` pasa de
y = −1,1 a −0,9, a la salida de la esquina. `reg2-cw` toca un pilar que no cambia: ese campo ya fallaba
sin aparcamiento en el lab.

**Causa (`reg1-cw`).** El color se conoce a tiempo. La línea planificada es la que no se puede seguir:
- la retención del pilar del asiento anterior mantiene +0,354 hasta 14,65;
- la esquina empieza en 14,85 con `d_a` = 0,25, que `corner.plan` elige porque da 4,8 cm de margen sobre el
  papel (con 0,35, 1,8 cm);
- la rampa de 0,2 m que baja 10 cm exige ~10 m⁻¹ de curvatura; el coche da 2,7. Sale mal orientado, satura
  la dirección en el arco y queda 5–10 cm por fuera del plan hasta tocar el pilar.

**Probado en el lab y revertido** (sin aparcamiento 0–49 × 2: línea base 89/100; con aparcamiento: 70/100):

| Cambio | Sin aparcamiento | Con aparcamiento | Qué pasó |
|---|---:|---:|---|
| `FREE_SHIFT` 0 / 0,05 (antes 0,10) | 77 / 84 | 63 / 61 | peor |
| Extremo libre hasta `OFFSET_LIMIT` (antes 0,3) | 89 | 70 | sin cambio: el plan sigue eligiendo 0,25 |
| Fijar el extremo si el vecino está en el asiento contiguo | 82 | 64 | choques con el muro exterior |
| Penalizar la rampa (0,5 m de margen por m) | 90 | 72 | arregla `reg1-cw` (5/5) y `reg2-cw` sin aparcamiento; rompe `reg4-cw`, `reg26-cw`, `reg30-cw` |

En `reg4-cw` con la penalización, el coche también va saturado toda la esquina y se sale 15–20 cm por
fuera. Es el mismo defecto: `corner.plan` puntúa la línea geométrica y no comprueba que el seguidor pueda
recorrerla (rampa previa, saturación y retardo del servo).

**Siguiente:** puntuar cada candidata por el recorrido simulado del seguidor (bicicleta con la curvatura
y la velocidad del servo limitadas, vectorizado sobre las candidatas), entrando con la rampa desde la
retención anterior.

## Iteración del 27 oct 2026: `corner.plan` puntuando el recorrido simulado (rama, no adoptado)

Código en la rama `obstacle-corner-tracked` (`f4c2482`), **no en `main`**.

**Qué hace.** Las mejores candidatas sobre el papel (12, más las que mantienen el desplazamiento del vecino)
se recorren con el seguidor de la misión simulado:
- referencia por progreso (el ángulo polar en la curva, como `mission._reference`);
- feed-forward y realimentación de `mission._steer`;
- servo real (0,06 s, 1,2 rad/s, 0,05 s) y límite de 0,307 rad;
- la línea más las rampas desde las retenciones vecinas;
- junto al hueco, las placas del aparcamiento en el margen (antes `corner.clearance` no las veía).

Gana el mayor margen recorrido. Se recalculan 17–24 esquinas por ronda, de 11–20 ms cada una (Mac).

**Fidelidad.** En `reg1-cw` la línea con rampa (`d_a` 0,25) da 4,7 cm sobre el papel y **0 cm recorrida**,
como el lab y Gazebo. La primera versión (punto más cercano en vez de progreso) no lo reproducía (5,1 cm).
Las esquinas S dan 2,0 y 2,3 cm recorridas (3,4 y 4,0 sobre el papel).

**Lab:**

| Set | `main` | Rama |
|---|---:|---:|
| Layouts 0–49 × 2 × semillas 0–2, sin aparcamiento | 265/300 | 264/300 |
| Layouts 0–9 × 2 × semillas 0–4, con aparcamiento | 70/100 (41,5 pts) | 72/100 (42,3 pts); 17 fallos de vuelta (antes 27), 8 toques de límite (antes 2) |

**Gazebo** (con aparcamiento, 1x, GPU):

| Campo | `main` (`v2-park-creep`) | Rama |
|---|---|---|
| `reg1-cw` | 18, empuja `sign_red_2` | **55 válida** (`v2-corner-tracked` y `v2-corner-lot`) |
| `reg2-cw` | 3, empuja `sign_red_1` | 13 y 22: toca `parking_limit_a` en las vueltas |
| `reg4-cw` | 55 válida | 40: toca un límite al aparcar (`v2-corner-lot`) |
| `reg0-ccw` | 55 válida | 40: no puntúa el aparcamiento (`v2-corner-lot`) |
| `reg4-ccw`, `reg8-ccw` | — | 55 válidas (`v2-corner-tracked`, sin las placas en el margen) |

**Probado y revertido en la rama:**
- Congelar la línea de una esquina en cuanto el coche entra: 70/100 y 54/100.
- Sí hace falta replanificar en plena curva: el color del pilar siguiente llega a veces dentro de la curva,
  y la simulación evalúa entrando desde la rampa, no desde donde está el coche (`reg4-ccw` del lab).

**Conclusión.** Arregla la clase de `reg1-cw` (rampa corta antes del arco), pero no mejora el total. Faltan:
- simular desde el estado real del coche cuando se replanifica en la curva;
- repetir Gazebo con varias rondas por campo, para saber si los aparcamientos perdidos son ruido.

## Fase 4: lo que queda

### 1. Semilla 0: resuelta y hallazgo corregido

El diagnóstico inicial de “límite solo cinético” estaba incompleto. En el primer escaneo la semilla
0 solo detectaba un pilar verde lejano (progreso 2,01), fijaba su offset y después ignoraba el verde
anterior (progreso 1,01) que aparecía en el escaneo siguiente.

**Corrección:** un latch activo puede sustituirse por un candidato claramente más cercano
(`PILLAR_SWITCH = 0,25` unidades de pista); las variaciones menores del mismo pilar conservan el
latch. No hace falta pre-posicionar ni aceptar el límite.

Resultado: las cinco semillas de `reg4-ccw` terminan con 40 puntos y sin contactos. Hay pruebas de
regresión para el reemplazo y para el ruido de distancia del mismo pilar.

### 2. Complejidad por función ≤ 10: cumplida

Medir con el mismo método:

```bash
python3 tools/code_metrics.py src/robotek_obstacle/robotek_obstacle/v2/*.py
```

Resultado: **299 líneas**, complejidad **98** y máximo **9**. `_run` se dividió en actualización de
pose, volante, velocidad y recuperación; `_next_pillar` se dividió en candidato y posición. Antes de
los cambios funcionales, los cinco JSON de `reg4-ccw` coincidieron bit a bit con la línea base.

### 3. Set completo de 10 en el laboratorio: ejecutado, criterio no alcanzado

Se ejecutaron las 10 geometrías del set estándar, cada una sobre su ronda más reciente de
`obs-base-a`.

| Campo | Puntos | Tiempo sim (s) | Válida | Margen | Fallo |
|---|---:|---:|---|---:|---|
| reg0-ccw | 40 | 97,50 | **sí** | 4,0 cm | — |
| reg0-cw | 1 | 6,60 | no | 0,0 cm | contacto con `sign_green_1` |
| reg1-ccw | 40 | 87,20 | **sí** | 5,1 cm | — |
| reg1-cw | 6 | 28,20 | no | 1,3 cm | lado incorrecto en `sign_red_1` |
| reg2-ccw | 4 | 16,00 | no | 3,2 cm | lado incorrecto en `sign_green_3` |
| reg2-cw | 0 | 1,00 | no | 0,0 cm | contacto con `sign_green_1` |
| reg3-ccw | 4 | 17,70 | no | 5,9 cm | lado incorrecto en `sign_green_2` |
| reg3-cw | 4 | 17,30 | no | 5,4 cm | lado incorrecto en `sign_red_1` |
| reg4-ccw | 40 | 107,00 | **sí** | 4,7 cm | — |
| reg4-cw | 4 | 13,00 | no | 0,0 cm | contacto con `sign_red_2` |

Resultado: **3/10 válidas**. Criterio de salida de la fase 4: **10/10 válidas** en el laboratorio,
40 puntos y sin contactos; **no cumplido**.
- Recordar que el laboratorio es un **filtro de un solo sentido**: 10/10 ahí no demuestra nada en
  Gazebo, pero fallar ahí es mala señal.
- Tabla y análisis guardados en `docs/obstacle-reimpl-v2.md`.

Hallazgos para la siguiente iteración:

- En CW ya se espejan clústeres, colores y volante, pero siguen apareciendo contactos o lados
  incorrectos en la primera vuelta.
- `reg2/3-ccw` muestran que seguir un carril desplazado no basta para secuencias de pilares en
  lados opuestos alrededor de una misma esquina.
- En algunos pilares la cámara entrega el color cuando el coche ya está a ~0,1 m lateral y no queda
  recorrido para alcanzar el offset. Frenar o apartarse más tampoco lo resolvió.
- Próximo diseño a medir: un waypoint de paso por pilar (antes/después de su línea) o una maniobra
  explícita de entrada/salida de esquina. No reducir `pillar_clearance` ni bajar más la velocidad
  sin repetir las cinco semillas.

### 4. Criterios de aceptación de la fase 4 (del plan)

- [ ] 10/10 válidas en el laboratorio con la dispersión que el filtro permita.
- [x] Tamaño: ≤ 360 líneas, ≤ 110 de complejidad, ≤ 10 por función, 11 parámetros, 3 estados.
- [x] Pruebas de capa 1 pasando (75 pruebas); falta una prueba de integración para cada patrón de
  pilares que aún falla.
- [x] Documentado qué falló y qué se cambió (este documento y
  [obstacle-reimpl-v2.md](obstacle-reimpl-v2.md)).

## Fase 5: nodo, launch y runner (`strategy:=v2`)

Objetivo: que el v2 corra en Gazebo con el mismo nombre de nodo, tópicos y archivos que el actual,
seleccionable con `strategy:=v2` / `--strategy v2`, **sin cambiar el valor por defecto**.

### Archivos que hay que tocar

| Archivo | Qué hacer |
|---|---|
| `src/robotek_obstacle/robotek_obstacle/v2/node.py` | **nuevo**: copia del nodo actual (`obstacle_strategy_node.py`) usando `v2.Mission`; mismo nombre de nodo `obstacle_strategy`, tópicos `/scan`, `/imu`, `/camera/image`, `/start`, `/cmd_vel`, `/robotek/state`, telemetría y *snapshots* iguales |
| `src/robotek_obstacle/config/obstacle_v2.yaml` | **nuevo**: los 11 parámetros del perfil (mismos defaults que `settings.py`) |
| `src/robotek_obstacle/setup.py` | entrada `obstacle_strategy_v2 = robotek_obstacle.v2.node:main` |
| `src/robotek_bringup/launch/obstacle_challenge.launch.py` | argumento `strategy` (`current`/`v2`) que elige ejecutable y `params_file` |
| `src/robotek_evaluation/tools/run_obstacle_gui_experiment.py` | `--strategy v2`; pasar el perfil y guardarlo en `manifest.json` |
| `src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh` | propagar el argumento |
| `src/robotek_evaluation/tools/clean_sim.sh` | añadir el patrón del ejecutable nuevo **antes** del primer lote |
| `src/robotek_evaluation/robotek_evaluation/obstacle_experiment_setup.py` | que el manifiesto registre `strategy` y el perfil usado |

Detalles que rompen rondas si se olvidan:

- **El juez busca `state == 'DONE'`.** El v2 usa `STOP`; el nodo (o la telemetría) debe escribir
  `DONE` al terminar, como ya hace el laboratorio.
- La telemetría necesita las **mismas columnas** (`x_track`, `y_track`, `progress`, `steer_actual`,
  `steer_right_actual`, `selected_direction`, …); si falta una, `int()` o el juez fallan.
- `done_hold` 32 s: la parada debe observarse ≥ 30 s.
- El nodo debe mantener el freno ante sensores viejos (`scan_max_age`, `imu_max_age`).
- No cambiar el valor por defecto del Obstacle: el `v2` se selecciona, no se impone.

### Verificación de la fase 5

1. Ronda de humo sin GUI: puntos, `validation` y `round.json` correctos.
2. Comparar con la misma ronda del actual (`python3 tools/compare_obstacle_suites.py`).
3. `clean_sim.sh` deja de matar procesos y `ps -Ao pid,command | grep obstacle_strategy`.

## Archivos de contexto para retomar

Léelos en este orden:

1. `AGENTS.md` — reglas de rondas, simulación honesta, git.
2. `docs/obstacle-reimpl-plan.md` — fases, criterios y decisiones del humano.
3. `docs/obstacle-reimpl-v2.md` — línea base, ablaciones, hallazgos, diseño y estado del v2.
4. `src/robotek_obstacle/robotek_obstacle/v2/mission.py`, `scene.py`, `settings.py` — el v2.
5. `src/robotek_obstacle/robotek_obstacle/obstacle_strategy_node.py` — interfaz a copiar (tópicos,
   control a 50 Hz, telemetría, `done_hold`).
6. `src/robotek_obstacle/robotek_obstacle/obstacle_recording.py` — columnas y *snapshots*.
7. `src/robotek_open/robotek_open/v5/node.py` — modelo de nodo con subpaquete.
8. `src/robotek_bringup/launch/obstacle_challenge.launch.py` y `open_challenge.launch.py` —
   modelo del interruptor `strategy:=`.
9. `src/robotek_evaluation/tools/run_obstacle_gui_experiment.{sh,py}` y `run_obstacle_batch.sh`.
10. `src/robotek_evaluation/tools/clean_sim.sh`.
11. `src/robotek_evaluation/robotek_evaluation/obstacle_lab.py` y `test/test_obstacle_lab.py` —
    laboratorio y su límite de fidelidad.
12. `tools/obstacle_suite_quiet.sh`, `tools/compare_obstacle_suites.py`, `tools/code_metrics.py`.

## Comandos

```bash
# Entorno y compilación
source tools/macos_env.sh >/dev/null 2>&1
colcon build --packages-select robotek_obstacle robotek_evaluation robotek_bringup
source install/setup.sh >/dev/null 2>&1

# Laboratorio: una ronda y el set de geometrías
python3 -m robotek_evaluation.obstacle_lab \
  --run docs/obstacle-challenge-runs/<ronda> --strategy v2 --compare
python3 -m robotek_evaluation.obstacle_lab --run <ronda> --strategy v2 --seed 0

# Pruebas
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=$(ls -d src/*/ | tr '\n' ':') \
  python3 -m pytest src/robotek_obstacle src/robotek_evaluation -q --ignore=src/rrc_lite_driver

# Tamaño
python3 tools/code_metrics.py src/robotek_obstacle/robotek_obstacle/v2/*.py

# Gazebo (fase 5/6), tras compilar
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh --name v2-smoke \
  --seed 0 --direction ccw --strategy v2 --steer-p-gain 20 \
  --launch-arg real_car:=true --no-gui --no-rviz --real-time-factor 1 --wall-timeout 320
```

## Decisiones abiertas (del humano)

1. **Velocidad**: 0,30 m/s cerca de pilares da ~107 s; el objetivo del plan es ≤ 110 s. Si se baja
   a 0,15 m/s el coche no cambia de lado a tiempo (medido).
2. **Margen lateral**: 0,12 m roza en 3/5 semillas; 0,18 m es el mínimo probado que pasa. No bajarlo
   sin repetir las 5 semillas.
3. **Push** a `main`: solo si se pide.
