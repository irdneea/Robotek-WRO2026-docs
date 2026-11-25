# Obstacle v3: ideas del top 3 de WRO FE 2025, probadas una a una

Rama `obstacle-v3`. Código en `src/robotek_obstacle/robotek_obstacle/v3/`, perfil `config/obstacle_v3.yaml`,
en Gazebo `--strategy v3`. Coche: URDF y `vehicle.py` de `2b17266` (el último, del `Assembly3.stp`).
Todas las pruebas pesadas se corrieron en la máquina remota ([maquina-remota.md](maquina-remota.md)).

## Punto de partida

El v3 empezó como **copia exacta del v2** (`a54247f`): mismas rondas en el lab, una a una. Cada idea se
añadió como parámetro **apagado por defecto** y se probó sola. Solo se activó lo que mejoró en dos sets de
semillas distintos.

## Qué hacen los tres primeros (final internacional 2025, Singapur)

Clasificación oficial: [scoring.wro-association.org/en/event/scoring/293](https://scoring.wro-association.org/en/event/scoring/293).
Los tres sacaron la puntuación máxima en Open (30) y Obstacle (62). El orden lo decidieron la
documentación (29,3 / 29,0 / 29,0) y el tiempo.

| Puesto | Equipo | Sensores | Navegación | Ideas que se pueden copiar |
|---|---|---|---|---|
| 1 | Double-X (Canadá), [repo](https://github.com/ejm22/WRO-FE-XX) | Solo cámara (Pi Camera 3 Wide); motor paso a paso (distancia sin encoder) | Reactiva: sigue el muro en la imagen; ante un pilar apunta a un punto del suelo a su lado | Prioridades de seguridad (giro de emergencia ante el muro exterior); acelerar entre pilares |
| 2 | KMIDS GFM (Tailandia), [repo](https://github.com/Chayanon-Ninyawee/KMIDS-GFM-Future-Engineer-2025) | LiDAR RPLIDAR S2, IMU BNO085, encoders, cámara 130° | PID de rumbo absoluto + PID de distancia al muro exterior con 4 objetivos; curvas como maniobra aparte | Mapa de pilares que solo acepta un pilar tras 3 lecturas iguales; +50 % de velocidad desde la vuelta 2 |
| 3 | STORMS NGR (Hungría), [repo](https://github.com/MoCsabi/WRO2025-FE-StormsNGR) | LiDAR 360°, giroscopio, encoders, cámara | Tramos rectos y giros de 90°; dos carriles; vuelta 1 de detección, después curvas de un solo arco | Ignorar la columna del pilar (dos carriles); terminar las curvas en el centro mientras no se conoce el color; color por defecto; una sola maniobra de aparcamiento |

Los tres miden la distancia con el motor (pasos o encoders); nosotros no tenemos encoder.

## Hipótesis y resultados

Lab con aparcamiento: layouts 0–49 × 2 sentidos × semillas 0–1 (200 rondas), que es el caso realista
(en la competición siempre hay aparcamiento). En la tabla, la base es el v3 idéntico al v2.

| # | Idea (origen) | Parámetro | Válidas | Pts medios | Tiempo | Veredicto |
|---|---|---|---:|---:|---:|---|
| — | Base (= v2) | — | 145 | 44,34 | 140,3 s | — |
| H1 | Más velocidad con el mapa conocido (KMIDS, STORMS) | `known_speed_gain` 1,2 / 1,4 / 1,6 | sin aparcamiento 261 / 252 / 240 de 300 (base 265) | — | −1,6 a −4,5 s | descartada: casi no ahorra tiempo y rompe rondas |
| H2 | Dos carriles fijos (STORMS, KMIDS) | `lane_offset` 0,26 / 0,30 | sin aparcamiento 239 / 224 de 300 | — | = | descartada |
| H4 | Guarda de contacto sobre el escaneo (Double-X) | `guard_gap` 0,02 / 0,03 | = base | = | = | no se dispara: el LiDAR (±110°, mínimo 16 cm) no ve los laterales |
| H4b | Guarda sobre el mapa y la pose | `guard_gap` 0,02 | 126 | 38,91 | = | descartada: retroceder a mitad de curva empeora |
| H6 | Tope de frente (0,2 m/s a < 0,7 m) más corto | `front_distance` 0,45 | 145 | 43,83 | **133,3 s** | más rápido, igual de válido, algo menos de puntos |
| H6 | Tope de frente más alto | `front_speed` 0,25 / 0,30 | 140 / — | 41,83 / — | 132,4 / 126,8 s | descartada |
| H7 | Feed-forward proporcional a la velocidad | `front_speed` 0,30 + `preview_time` 0,5 | 121 | 37,09 | 126,8 s | descartada |
| H3 | Esquinas puntuadas por el recorrido simulado (rama `obstacle-corner-tracked`) | `tracked_corners` 1 | 149 | 44,88 | 140,9 s | mejora |
| H8 | Despacio en esquinas planificadas con poco margen (STORMS: precisión donde importa) | `tight_gap` 0,07, `tight_speed` 0,15 | 143 | 44,58 | 141,9 s | mejora poco sola |
| **c3** | **H3 + H8 con margen 0,09** | `tracked_corners` 1, `tight_gap` 0,09, `tight_speed` 0,15 | **156** | **46,38** | 151,6 s | **adoptada** |
| c4 | H3 + H8 (0,07) + `front_distance` 0,55 | | 156 | 46,20 | 141,9 s | segunda; peor en semillas nuevas |

**Validación con semillas nuevas (2–3, nadie ajustó con ellas):** base 149 / 44,79 pts; **c3 156 / 46,40**;
c4 155 / 45,56; c3 + `front_distance` 0,55: 146 / 44,63. Sin aparcamiento (0–49 × 2 × semillas 0–2): c3
**270/300** frente a 265.

**Más variantes, sobre la elegida (semillas 0–1 / 2–3):**

| Cambio sobre c3 | Válidas | Pts medios | Tiempo | Veredicto |
|---|---|---|---|---|
| `park_speed` 0,08 / 0,10 (semillas 2–3) | 99 / 11 | 42,49 / 35,84 | 144,5 / 147,7 s | descartada: aparcar a 0,06 m/s sigue haciendo falta |
| `front_distance` 0,60 | 153 / 149 | 45,32 / 45,43 | 149,8 s | descartada |
| `front_distance` 0,65 | 151 / 149 | 45,96 / 45,19 | 150,5 s | descartada |
| `corner_replan` 0 (sin replanificar en la curva) | 148 / 155 | 45,52 / 46,48 | 151 s | se mantiene la replanificación |
| Simulación del seguidor con paso de 0,04 s y 6 candidatas (más barata) | 147 / 151 | 45,51 / 45,62 | 150,5 s | descartada: la fidelidad importa |

### Coste en el coche

`corner.plan` simula el seguidor: 21 ms de mediana y hasta 73 ms en el Ryzen de la remota, 30–40 veces por
ronda. En la Pi del coche serían 3–5 veces más. Como sus argumentos son discretos (pilares a ±0,1 con 3
estados de color, desplazamientos vecinos redondeados a 1 cm, la rampa corta y el hueco), se precalculan:
`tools/build_corner_table.py` escribe `v3/corner_table.py` con las 1083 combinaciones (2,4 s en la remota).
En el lab no falta ninguna y los resultados son idénticos en 200 rondas. Solo se calculan en marcha las
replanificaciones dentro de la curva: 4–8 por ronda, de 27 ms como mucho en el Ryzen.
`test_v3_corner_table` avisa si la tabla queda desactualizada.

### Tiempo y límite de 180 s

c3 es ~11 s más lento: 36 de sus rondas válidas del lab pasan de 160 s (v2: 4) y 2 se quedan sin tiempo.
En Gazebo, que va más lento que el lab, `reg3-cw` llegó a 180 s sin terminar de aparcar. Por eso se
comparó también c4 en Gazebo.

### Hallazgos

- **El tiempo no está en la velocidad de crucero.** En una ronda de ~100 s, el tope «algo a menos de 0,7 m
  → 0,2 m/s» ocupa 45–88 s; a crucero el coche va menos de 2 s. Por eso subir la velocidad (H1) no ahorra
  casi nada. Para ir más rápido hay que curvar más rápido, y el seguidor no aguanta 0,30 m/s en curva (H6,
  H7).
- **El 21 % de las rondas con aparcamiento fallan en las vueltas**, 3 de cada 4 en CW, casi todas por
  contacto con un pilar. Son deterministas (las dos semillas fallan igual). La mitad son de la primera
  vuelta y la clase principal es la esquina S (pilar interior al entrar, exterior al salir).
- **Lo que funcionó** ataca justo eso: elegir líneas de esquina que el coche puede seguir (H3) e ir
  despacio en las esquinas estrechas (H8). c3 baja los fallos de vuelta de 43 a 30 de 200.
- La guarda reactiva de Double-X no se puede copiar tal cual: su cámara ve delante y nuestro LiDAR no ve los
  laterales del coche.

## Gazebo

Set estándar con aparcamiento (layouts 0–4, los dos sentidos), 2 rondas a la vez, 1x, GPU.

| Estrategia | Válidas | Pts medios | Puerta de calidad | Fallos |
|---|---|---|---|---|
| v2 (`v2-gz`) | 5/10 | 34,8 | 8/10 | `reg0-cw` 1, `reg1-cw` 18, `reg2-ccw` 11, `reg2-cw` 3, `reg4-cw` 40 |
| v3 c3 sin tabla (`v3-gz`) | 6/10 | 38,0 | 6/10 | `reg1-cw` 6, `reg2-ccw` 3, `reg3-cw` 37 (sin tiempo), `reg4-cw` 4 |
| v3 c3 con tabla (`v3c3-gz`) | 6/10 | 41,7 | **10/10** | `reg1-cw` 6, `reg2-cw` 40, `reg3-cw` 37 (180 s), `reg4-cw` 4 |
| **v3 c4 (`v3c4-gz`, por defecto)** | **8/10** | **45,0** | **10/10** | `reg1-cw` 6, `reg4-cw` 4 |

- La tabla de esquinas eliminó los fallos de la puerta de calidad (huecos del bucle de 0,22–0,30 s).
- `v3-gz2` se paró a medias: corrió a la vez que un barrido del lab en la misma máquina (carga 29). Sus
  rondas están en el registro pero no cuentan.
- `reg1-cw` (empuja `sign_red_1` a 36–38 s) y `reg4-cw` (lado incorrecto en `sign_red_2` a 16 s) fallan en
  Gazebo con c3 y con c4, pero pasan en el lab: hay que mirar la cámara de Gazebo en esos dos campos.

## Decisión

**v3 = c4**: `tracked_corners` 1, `tight_gap` 0,07, `tight_speed` 0,15, `front_distance` 0,55; el resto
igual que el v2.
- En Gazebo, primero por puntos (45,0 frente a 41,7 de c3 y 34,8 del v2) y después por tiempo (127–171 s).
- En el lab con aparcamiento: 155/200 y 45,56 pts (semillas 2–3; v2 149 y 44,79), sin rondas sin tiempo.
  c3 daba 0,5 pts más en el lab, pero 36 de sus rondas válidas pasaban de 160 s y en Gazebo se queda sin
  tiempo.
- Sin aparcamiento queda algo por debajo del v2 (261 frente a 265 de 300). En la competición siempre hay
  aparcamiento.

## Iteración del 1 nov 2026 (tarde): `reg1-cw`/`reg4-cw` y las esquinas S

### `reg1-cw` y `reg4-cw` no eran de Gazebo

Con aparcamiento, el lab **también** falla en esos dos campos. La causa está en el plan:
- La esquina se planificaba mientras el pilar del asiento contiguo (4,5) aún no tenía color, y la salida iba
  hacia fuera (−0,12).
- Cuando llegaba el verde (+0,354), quedaban 0,25 m para desplazarse 0,47 m.
- La simulación de la esquina no veía ese pilar vecino: medía el margen solo con los de sus asientos, la isla y
  los muros, así que cualquier salida le parecía buena, también al replanificar.

Arreglo (`3eecc3a`):
- **El pilar del asiento contiguo entra en la simulación**, con su lado. `pin` lleva su lateral y su color, y
  la simulación recorre hasta pasarlo.
- **Un pilar de color desconocido se aborda por el centro** (`unknown_offset` 0, idea de STORMS; el v2 se
  apartaba 0,12 m).

Resultado: con aparcamiento, 153 y 151 de 200 válidas con **47,22 pts** en los dos sets (antes 46,20 y 45,56).
`reg1-cw` pasa a 55 en las dos semillas.

### Esquinas S: líneas buscadas

Los fallos fijos que quedaban (7 campos, todos CW) eran esquinas S: un pilar por el lado de la isla al
entrar y otro por fuera al salir.
- La mejor línea recta‑arco‑recta deja 1–2 cm recorridos, menos que el ruido de localización.
- Una búsqueda A\* (solo hacia delante, radio ≥ 0,5 m) encuentra trayectorias con una recta en diagonal dentro
  de la esquina, que la familia no puede representar. La mejor deja **4,6 cm recorridos** donde la familia
  dejaba 2,0.
- El generador de la tabla la busca para cada esquina con menos de 3,5 cm recorridos. Los pilares, los vecinos
  y los límites del hueco son obstáculos, con un muro virtual en el lado prohibido de cada pilar de color
  conocido. Solo se guarda si recorrida mejora a la familia en 0,5 cm: pasa en 223 de 867 esquinas, con
  mediana de 3,9 cm.
- La ronda sigue sin buscar nada: consulta la tabla.

| Lab | Antes | Con líneas buscadas (`7a02bae`) |
|---|---|---|
| Con aparcamiento, semillas 0–1 | 153/200, 47,22 pts | **162/200, 49,51 pts** |
| Con aparcamiento, semillas 2–3 | 151/200, 47,22 pts | **154/200, 48,84 pts** |
| Sin aparcamiento, 0–49 × 2 × semillas 0–2 | 261/300 | **291/300** |

Se arreglan las S de `reg0`, `reg6`, `reg7`, `reg12`, `reg21` y `reg47` (CW) y se rompen `reg16-cw`, `reg17-cw`
y `reg27-cw`.

**Gazebo** (con aparcamiento, 2 a la vez, 1x, GPU, 16/16 rondas limpias):

| Set | Resultado |
|---|---|
| Estándar (`v3s-gz`) | **7/10 válidas, 46,5 pts de media** (antes, c4: 8/10, 45,0). `reg1-cw` 55 (176 s); `reg4-cw` 40 (no puntúa el aparcamiento); `reg2-ccw` 3 (contacto a 29 s); `reg3-cw` 37 (sin tiempo a 180 s) |
| Campos S y los que se rompían en el lab (`v3s-gz-x`) | **6/6 válidas**: `reg6`, `reg12`, `reg21`, `reg47`, `reg16` y `reg27` (CW), 138–168 s |

## Iteración del 8 nov 2026: el coche real con el motor controlado (`--car real_v3`)

El motor del coche ya controla la velocidad (M2 sin tipo de motor, 54:30, 4,4 rps por m/s). Nuevo perfil del lab
`real_v3`; detalle y evidencia en [obstacle-estado.md](obstacle-estado.md#coche-real-en-el-lab---car-real_v3-8-nov-2026).

| Cambio | Hallazgo | Resultado |
|---|---|---|
| Línea base `real_v3`, capas 0–49, semillas 0–1 / 2–3 | Las vueltas funcionan: 192 / 195 de 200, ~124 s (Gazebo 194, 109 s) | Referencia |
| Línea base con aparcamiento | 8/200 (Gazebo 156/200): 132 rondas aparcan «en parte o no paralelo», también con 300 s | Problema nuevo, el mayor |
| Aparcamiento: sensibilidad | Sin retraso del motor 68/100; `steer_gain=1.0` 38/100; `park_speed` 0,04 → 13/100 (Gazebo 46/100), 0,10 → 0/100 | `park.py` debe tener en cuenta el retraso del motor y el radio real |
| `approach_max` 0,35 / 0,5 / 0,7 rad (tope del rumbo hacia la línea) | En la ronda 2 baja el rumbo de 48° a 20–40°, pero el margen no mejora | 177 / 191 / 192 en `real_v3`, 177 / 194 / 192 en Gazebo: **descartado y quitado** |
| `start_ramp` 0,5 / 1,0 (la línea empieza en el desvío real) | Primera versión: solo una rampa de 0,06 unidades (la línea de la esquina anterior ya tenía el desvío); luego quitaba la zona de mantenimiento del pilar (166/200); luego, con un pilar junto a la salida, lo rozaba | Versión final: 194/200 en `real_v3` (+2, `reg1-ccw`), 194 en Gazebo; semillas 2–3 iguales; con aparcamiento −1 / −2. **Opción apagada por defecto** |
| `park_replan=1` (replanificar el aparcamiento desde la pose del coche) | 100 rondas, semilla 0: 46–50/100 (de 4). Primera versión no determinista (límite por reloj de pared): se cambió a un tope de 6000 nodos. Esperar quieto antes de replanificar: más rondas sin tiempo, quitado | Ayuda en `real_v3` |
| + `park_approach_speed=0.25` (ir más rápido hacia el lote y en los retrocesos largos) | 52/100; con `known_speed_gain=1.5`, 63/100. Quedan ~12 toques del límite, ~14 sin tiempo y 3 contactos con el primer pilar. El aparcamiento empieza a 90–147 s; ir hasta el plan cuesta 11–28 s y la maniobra 30–45 s | |
| Validación, capas 0–49 × 2, con aparcamiento, semillas 0–1 / 2–3 | `real_v3` 102 / 107 (de 8 / 7), con `known_speed_gain` 120 / 117; Gazebo 131 / 126 (de 156 / 161), con `known_speed_gain` 127 / 133; sin aparcamiento iguales (con `known_speed_gain`, −2 a −6) | **Apagado por defecto** (empeora Gazebo); el aparcamiento fijo (`park_mode: 1`) da 138/200 en `real_v3` |

Hallazgos:
- El caso de la ronda 2 del 4 nov (salto lateral de 0,30 m a la salida) en el lab solo hace daño con el coche
  embalado. A 0,15–0,30 m/s reales, `real_v3` pasa el campo de la ronda 2 con 9,7 cm.
- Ningún cambio portado a robotek-learn: ninguno mejora los dos coches. Para aparcar en el coche, el candidato es el
  aparcamiento fijo ([obstacle-aparcamiento-fijo.md](obstacle-aparcamiento-fijo.md)); `park_replan` y
  `park_approach_speed` quedan como opciones del planificador.

## Lo que queda

- `reg1-cw` y `reg4-cw` en Gazebo (cámara o color tardío; el lab las pasa).
- Las esquinas S siguen siendo el grueso de los fallos (33 de 200 en el lab). Lo siguiente sería una
  maniobra con marcha atrás, como el retroceso de STORMS cuando llega tarde a una curva.
- El tiempo (~142 s con aparcamiento) está lejos de los 49–63 s del top 3. Necesita curvas más rápidas: un
  seguidor que aguante 0,30 m/s en curva o una medida de distancia directa (encoder).
- Repetir Gazebo con más rondas por campo y validar con GUI en el Mac antes de darlo por candidato final.
