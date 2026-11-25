# Obstacle Challenge — reglas y cómo realizarlo (WRO 2026 Future Engineers)

Recopilación de las reglas del **Obstacle Challenge** (Reglas Generales 2026 y
Especificaciones del Campo) y de un plan de implementación para Robotek, con lo que
hacen los 3 mejores equipos del Mundial 2025
([referencias](../referencias/README.md)).

> Fuente local: `docs/WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md`
> (§9, §10, §13 y Apéndice A) y `docs/WRO-2026-Future-Engineers-Gamefield-Specifications.md`.
> Los números de regla (§) y figura remiten a esos documentos.

## 1. Qué es

La misma pista del Open (3×3 m, isla central, 8 secciones) pero con **señales de
tráfico** (pilares rojo/verde) y una **zona de aparcamiento**. El vehículo debe dar
**3 vueltas** respetando las señales y, al terminar, **aparcar en paralelo**. Duración
de ronda: **3 minutos** (§9.2). Máximo: **62 puntos** (§10.2.2).

## 2. Pista y elementos

- **Corredor:** 1000 mm fijo (±10 mm en la final) — a diferencia del Open, **no se
  estrecha** (§ "Obstacle Challenge rounds").
- **Señales (pilares):** 50×50×100 mm (§13.19). **Rojo** RGB(238, 39, 55) (§13.21),
  **verde** RGB(68, 214, 44) (§13.22). Asiento 50×50 mm (§13.13) y un **círculo** de
  evaluación alrededor del asiento (§13.14).
- **Aparcamiento:** ancho siempre **20 cm**; largo = **1,5 × largo del robot** (§ pista).
  Limitado por **dos elementos magenta** de 200×20×100 mm (§13.25, §13.27). Siempre en
  la **sección de salida**.
- **4 T-intersecciones y 2 X-intersecciones** por sección recta definen las posiciones
  posibles de las señales.

## 3. Randomización (antes de cada ronda, tras el check time)

1. **Sentido** de conducción (CW/CCW): aleatorio (§9.3).
2. **Sección de salida**: 2 lanzamientos de moneda.
3. **Señal única**: 2 monedas eligen la sección; 1 moneda el color (cara=verde, cruz=rojo).
4. **Resto de señales**: 36 cartas (se quita la 9 si verde / la 10 si rojo) → se reparten
   sin reemplazo para cada sección recta siguiente (en sentido horario).
5. **Aparcamiento**: siempre en la sección de salida (otro par de monedas). Tras
   colocarlo, las señales de esa sección se **mueven más cerca del muro interior**.
6. El equipo decide **arrancar dentro del aparcamiento** (puntos extra) o en la **zona
   central encima** (§, figura 8a). Los puntos por arrancar en el aparcamiento solo se
   otorgan si se completa **≥1 vuelta**.

## 4. Reglas de conducción durante la ronda

- **§9.19** — El **vehículo pasa por la derecha del rojo y por la izquierda del verde**,
  referido al sentido de circulación. Apéndice A §5 aclara el lado incorrecto: es falta cruzar el radio
  "por el lado derecho del pilar verde" (Fig. 29) o "por el lado izquierdo del rojo"
  (Fig. 30). Es decir: **verde → pasar dejándolo a la derecha del coche; rojo →
  dejándolo a la izquierda**. *Verificar la lateralidad con las figuras antes de fijar
  el signo del controlador.*
- **§9.20** — Se **puede tocar/mover/tumbar** una señal mientras su proyección esté
  **dentro del círculo** del asiento (no puntúa como "movida"). Fuera del círculo sí
  cuenta como movida.
- **§9.21** — Se permite circular en **sentido contrario** solo por **2 secciones**
  (la del cambio y la vecina).
- Las señales **solo se obedecen en las 3 vueltas oficiales**. En la ruta posterior al
  aparcamiento se pueden **esquivar por cualquier lado**, pero **no se pueden mover**.
- **No se pueden tocar los límites del aparcamiento** (§6 de Apéndice A): si se tocan,
  el robot se detiene y **no se puntúa el aparcamiento**.

## 5. Fin de ronda / faltas (§9.24)

Termina la ronda cuando:

- **9.24.4** — Tras 3 vueltas correctas, el vehículo **se detiene** en la sección
  correcta **o en el aparcamiento**.
- **9.24.5** — Tras pasar una señal **por el lado incorrecto**, cruza **completamente el
  radio** de interior a exterior en la posición de la señal.
- **9.24.6** — El robot **movió una señal fuera del círculo**.
- **9.24.7** — El robot **toca los límites del aparcamiento**.
- También §9.24.1 (tiempo), §9.24.8–13 (reparaciones, tocar el campo, salirse/deteriorar).

## 6. Puntuación (máx. 62) — §10.2.2

Base común con el Open (30): 1.1 conducir en sentido de la ronda (1 c/u, 24),
1.2 vuelta completa (3), 1.3 parada en la sección de llegada (3).
**Puntos adicionales del Obstacle:**

| Ítem | Requisito | Pts |
|---|---|---:|
| 1.4 | Señal(es) movida(s), **sin** completar 3 vueltas (mín. 1 vuelta) | 2 |
| 1.5 | Señales **no** movidas, sin completar 3 vueltas (mín. 1 vuelta) | 4 |
| 1.6 | Tras 3 vueltas: señal(es) **movida(s)** | 8 |
| 1.7 | Tras 3 vueltas: **ninguna** señal movida | 10 |
| 1.8.1 | Arrancó **dentro del aparcamiento** y completó ≥1 vuelta | 7 |
| 1.8.2 | **Aparcó** completamente dentro y **paralelo** | 15 |
| 1.8.3 | Aparcó **parcial** o **no paralelo** | 7 |

- Reparación (sacar el coche del campo): total de la ronda **÷2**.
- La nota general = mejor Open + mejor Obstacle + documentación (máx. 122).
- Desempate: primero Obstacle (puntos y luego tiempo), después documentación, después
  Open (§10.8).

## 7. Aparcamiento (Apéndice A §6)

- **Completamente aparcado**: la **proyección** del robot está **totalmente dentro** del
  rectángulo entre los dos marcadores **y** queda **paralelo** al muro del campo.
- **Paralelo** = la distancia de las **dos ruedas de un mismo lado** al muro **no difiere
  más de 2 cm**. Se miden las dos ruedas motrices.
- **Parcial**: la proyección está solo **parcialmente** dentro.
- **Tocar los límites** del aparcamiento → sin puntos de aparcamiento y ronda detenida.

## 8. Significado de "movida / tumbada" (Apéndice A §1)

(a) no movida · (b) fuera del asiento pero **dentro** del círculo (no cuenta como movida)
· (c) parcialmente fuera del círculo → **movida** · (d) tumbada parcialmente fuera ·
(e) movida completamente fuera → **para la ronda** · (f) tumbada completamente fuera →
**para la ronda**.

## 9. Cómo realizarlo (plan para Robotek)

Nuestro stack actual (LiDAR + IMU, con cámara) sirve: se reutiliza la conducción del
Open (cruce/giro/velocidad) y se añaden **percepción de señales** y **aparcamiento**.

### 9.1 Percepción de señales
- **Color (cámara):** segmentar **rojo y verde** en HSV (el rojo/verde de la pista son
  saturados: 238/39/55 y 68/214/44). Filtrar por tamaño/forma (pilar ~50×100 mm) y por
  la banda donde caen los objetos (suelo), no el muro.
- **Geometría (LiDAR):** detectar el **cluster** del pilar (puntos cerca de 0.05 m por
  proximidad) y su **posición/distancia**. Cruzar color de cámara con el bearing del
  cluster para **asociar color ↔ posición** (este cruce cámara-LiDAR es lo que hacen
  KMIDS y STORMS).
- Alternativa sin cámara: el pilar es un objeto **más bajo y aislado** que el muro;
  se puede detectar por altura/cluster, pero **el color exige cámara**.

### 9.2 Decisión de paso
- **Rojo → pasar por su derecha** (queda a la izquierda del coche); **verde → por su
  izquierda** (queda a la derecha). Añadir un **sesgo de rumbo** hacia el lado correcto
  al acercarse, con distancia calculada para **no** tocar el pilar (tocarlo dentro del
  círculo no penaliza, pero moverlo fuera del círculo **para la ronda**).
- Medir el **hueco** a cada lado del pilar con LiDAR y elegir el lado permitido.
- Mantener el **carril/corredor** (1000 mm fijo) con el lazo actual.

### 9.3 Vueltas y llegada
- Igual que el Open para contar 3 vueltas y mantener el sentido.
- Tras las 3 vueltas, **ir al aparcamiento** (sección de salida); las señales se pueden
  esquivar libremente pero **no mover**.

### 9.4 Aparcamiento (lo más caro: 15 pts)
- Detectar los **dos límites magenta** (color 255,0,255) + su geometría (LiDAR).
- Maniobra tipo STORMS: **una secuencia de arcos de Ackermann** calibrada para entrar al
  aparcamiento (≈0,24 m/s) tras detenerse frente a él; alinear **paralelo** midiendo la
  distancia de **ambas ruedas al muro exterior** (criterio ≤2 cm de diferencia) y
  centrar la proyección dentro del rectángulo.
- Asegurar un **stop** final (no seguir moviéndose; regla de los 15 s como en Open).
- Considerar arrancar **dentro del aparcamiento** (+7) si se completa ≥1 vuelta.

### 9.5 Qué hacen los 3 mejores (2025)
- **Double-X (1º):** cámara; arbitraje por prioridad `choose_output_angle`: choque con
  muro exterior → giro de emergencia; esquivar obstáculo según color; muro interior
  demasiado cerca → volver a wall-following; si no, wall-following. Conteo de vueltas
  con máscaras azul/naranja; aparcamiento por cámara (reconoce que le faltan sensores
  laterales de distancia).
- **KMIDS GFM (2º):** convierte los puntos LiDAR a cartesianas, filtra regiones de muro
  (`outerEdge 0.30 m`, `innerEdge 0.70 m`), agrupa por proximidad (~0.05 m) y **cruza con
  bloques de color** (HSV rojo/verde/rosa) para localizar las señales.
- **STORMS NGR (3º):** color por cámara (OpenCV); **Ackermann calibrada para salir/entrar
  del aparcamiento en un arco continuo**; Obstacle a ~0,65 m/s; `predictedYaw` y
  *phantom distance* para compensar latencia y deadzone del LiDAR.

## 10. Open vs Obstacle (diferencias)

| | Open | Obstacle |
|---|---|---|
| Señales | No | Pilares rojo/verde |
| Aparcamiento | No (parada en zona) | Sí, en paralelo |
| Corredor | 1000 mm (muros interiores aleatorizados) | 1000 mm fijo |
| Máximo de puntos | 30 | **62** |
| Fin | parada en sección de llegada | parada o **aparcar** |

## 11. Estado en Robotek

Hoy **no hay lógica de Obstacle** implementada (`src/robotek_control` cubre el Open).
Ya existe el lanzador `src/robotek_bringup/launch/obstacle_challenge.launch.py`
(levanta el mundo `field:=obstacle`; el `strategy` por defecto es `open_strategy`,
sin señales/aparcamiento todavía).
Puntos de partida reutilizables: percepción LiDAR/IMU, lazo de control, conteo de giros,
parada de 30 s en reloj de simulación. Añadir: percepción de color (cámara), asociación
cámara-LiDAR, decisión rojo/verde y maniobra de aparcamiento. Ver
[carril/frenado/alineación](next-steps.md) y [análisis del top 3](../referencias/04-analisis-codigo-open-challenge.md).

## 12. Top 3 del Mundial 2025 — tiempos y estrategias de Obstacle

### Tiempos (ronda = 3 vueltas + aparcamiento)

| Equipo | Ronda 1 (s) | Ronda 2 (s) | **Mejor (s)** | Pts Obstacle |
|---|---:|---:|---:|---:|
| 🥇 Double-X 🇨🇦 | 63 | 49 | **49** | 62 |
| 🥈 KMIDS GFM 🇹🇭 | 60 | 63 | **60** | 62 |
| 🥉 STORMS NGR 🇭🇺 | 87 | 69 | **69** | 62 |

Los tres puntuaron el máximo (62). Double-X suma 121,3 frente a 121 de los
otros dos por su documentación (29,3 frente a 29,0); no ganó exclusivamente
por el tiempo de Obstacle. Los tiempos sirven como referencia de esas rondas.

### Double-X (1º) — solo cámara

- Estados: `CHALLENGE_2_FIND_DIRECTION → CHALLENGE_2_LAPS → CHALLENGE_2_APPROACH
  → CHALLENGE_2_FORWARD → CHALLENGE_2_BACKWARDS`.
- `find_obstacle_angle_and_draw_lines()` devuelve el ángulo de esquiva + `is_green`;
  `calculate_servo_angle_from_obstacle(angle, is_green)`; arbitraje
  `choose_output_angle(walls, obstacles)` (choque con muro exterior → giro de
  emergencia; obstáculo; muro interior; si no, wall-following).
- Velocidades por fase: obstáculos 5000, muros 4500, approach 2500, aparcamiento 2000,
  aparcamiento acelerado 4500.
- En `APPROACH` detecta el **límite rosa** (`find_pink_obstacle_angle`) y decide si seguir
  el muro rosa o el obstáculo; recuerda el último color tras la 3ª vuelta.
- Aparcamiento: `FORWARD → BACKWARDS → PARKING` con un punto central del suelo y la línea naranja.

### KMIDS GFM (2º) — cámara (color) + LiDAR (geometría)

- Máquina de estados con fases de **unpark** (CCW/CW), `NORMAL→PRE_TURN→TURNING`, y una
  secuencia larga de aparcamiento (`*_FIND_PARKING`, `PARKING_1..3`, u-turn previo).
- **Fusión de señales**: `filterColors` (HSV) → `computeBlockAngles` (bearing por bloque
  de color) cruzado con `getTrafficLightPoints` (LiDAR) → `combineTrafficLightInfo` →
  `classifyTrafficLights` (segmento y lado inner/outer); **historial de 3** detecciones
  para confirmar color↔posición en un mapa.
- Conducción: sigue el **muro exterior** con distancia objetivo que **depende del color y
  del lado** de la señal (0.25–0.76 m), con PID de rumbo + PID de muro. `PRE_TURN` a
  1.20 m; umbral de giro **según la señal siguiente** (0.50–1.07 m) y modo *push* (4.5)
  a partir del giro 5.
- Aparcamiento: al giro 12 decide la ruta según la señal (rojo/verde), con **u-turn** si
  hace falta; localiza las **paredes del aparcamiento** con LiDAR (`getParkingWalls`) y
  maniobra `PARKING_1..3`.

### STORMS NGR (3º) — cámara color + LiDAR, carril y arcos

- `obstacleChallengeRun()`: sale del **aparcamiento con arcos** según el sentido, detecta
  la primera señal (`findNearestObject` + `detectObjectColor`) y guarda una **matriz de
  señales** por sección/fila/columna.
- Carril: `switchLane(LANE_LEFT si GREEN else LANE_RIGHT)`; detecta por filas y puede
  cambiar de carril dentro de la sección; `correctWallDist` al muro.
- Velocidades: Obstacle ≈0,65 m/s; aparcamiento ≈0,24 m/s. `predictedYaw` y
  *phantom distance*.
- `parkingManouver(firstSignColor)`: evita la primera señal si está en el camino,
  alinea con muro/paredes, **arco de 90°**, avanza hasta 20 cm del muro frontal,
  retrocede y ejecuta el **arco de aparcamiento con parada de emergencia** si la
  distancia calculada al muro es <2 cm; termina avanzando hasta 15,5 cm y para.

### Lecciones

- Los tres usan **cámara para el color**. **Double-X no usa LiDAR**; KMIDS fusiona
  cámara y LiDAR, y STORMS usa LiDAR para objetos/carril y cámara para su color.
- **El aparcamiento es lo más caro (15 pts)** y donde más varían: KMIDS/STORMS usan arcos
  + búsqueda de paredes; Double-X, geometría de imagen y líneas del suelo.
- No mover señales (10 pts) y el orden de vueltas son los otros puntos clave; los tres
  lograron 62.

## 13. Referencias

- [Reglas Generales 2026 (local)](WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md) — §9.19–9.24, §10.2, §13, Apéndice A §1/§5/§6.
- [Especificaciones del campo](WRO-2026-Future-Engineers-Gamefield-Specifications.md).
- [Reglas Open (resumen, local)](WRO-2026-Future-Engineers-Open-Challenge-Rules.md).
- [Top 3 Mundial 2025](../referencias/README.md) y [análisis de código](../referencias/04-analisis-codigo-open-challenge.md).


## 14. Investigación actualizada y separación de controladores

[Análisis del código Obstacle de los tres equipos](../referencias/05-analisis-codigo-obstacle-challenge.md):
fuentes fijadas a commits, fusión, carriles, parking y adaptación a ±25°.
Por instrucción del usuario, Obstacle se implementará en `obstacle_strategy`
y módulos, YAML, runner y registros separados de Open. El lanzador actual
continúa apuntando a Open hasta que exista el nuevo ejecutable; todavía no
hubo una ronda Obstacle válida.

Antes de validar aparcamiento, corregir/generar el hueco del mundo Obstacle:
actualmente es 43 cm entre caras; el robot recto tiene una proyección relevante
aproximada de 19 cm, que implica 28,5 cm a 1,5×L. Confirmar largo real y Q&A.
