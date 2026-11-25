# Obstacle v2: línea base, investigación y reimplementación

Estado: **en curso** (22 oct 2026). Este documento registra la ejecución del
[plan del Obstacle v2](obstacle-reimpl-plan.md): línea base, hallazgos, diseño y resultados.
El plan sigue siendo la guía; aquí solo van los datos y las decisiones tomadas.

## Fase 0 · Línea base y herramientas de medida

### Criterio de ronda válida (decisión del usuario, 21 oct 2026)

Se mantiene el criterio actual de `rule_judge.standard_validation`:

- 40 puntos estimados (máximo sin aparcamiento) y sin faltas de reglamento;
- sin contactos según los sensores de Gazebo;
- parada observada ≥ 30 s;
- margen mínimo ≥ 1 cm (muestreado a la frecuencia de telemetría);
- dirección máxima ≤ 25,5°.

«Cómodo» (≥ 5 cm) y «justo» (2–5 cm) son clases informativas, no el umbral de validez.
Tolerancia de tiempo para comparar el v2: **+10 % de la media** (valor por defecto del plan).

### Medidas de tamaño de la estrategia actual

Método: `tools/code_metrics.py` (plan §9), sin comentarios ni docstrings.

| Conjunto | Líneas | Complejidad | Función más compleja |
|---|---|---|---|
| Misión + driver + planificador + localizador + mapa + percepción + campo | 723 | 227 | 15 |
| Aparcamiento (`obstacle_parking.py`) | 303 | 124 | 30 |
| Nodos ROS (`obstacle_strategy_node.py`, `obstacle_detector_node.py`) | 347 | 88 | 19 |
| **Total sin aparcamiento** | **1.070** | **315** | **19** |
| Total con aparcamiento | 1.373 | 439 | 30 |

Configuración: **16 parámetros ROS** y **32 valores fijos** (`ObstacleConfig`).
El perfil activo (`obstacle_sensors_v1.yaml`) solo fija `direction: auto`.
Estados del driver: `PLAN`, `PLAN_RECOVER`, `PLAN_BLOCKED`, `FINISH`, `DONE` (más
`CALIBRATE`/`DETECT_DIRECTION` en la misión).

### Herramientas nuevas

| Herramienta | Qué hace |
|---|---|
| `tools/code_metrics.py` | Líneas, complejidad total y máxima por archivo, con el método del plan §9 |
| `tools/compare_obstacle_suites.py` | Compara sets por `reg<semilla>-<sentido>`: puntos, validez, margen y tiempo frente a la dispersión de referencia |
| `tools/obstacle_suite_quiet.sh` | Set estándar de 10 rondas con puerta de carga ≤ 8 y repetición (hasta 3) si el nodo se atrasa en **toda** la ronda |

Trampa de entorno encontrada al estrenar la suite: `set -u` en el script + `source tools/macos_env.sh`
(que sourcea `install/setup.bash`) aborta con `COLCON_TRACE: unbound variable`. La suite no usa `set -u`.

### Línea base en Gazebo

Dos corridas del set estándar (semillas 0–4 × CCW/CW) con la estrategia actual, con la puerta de
calidad. La diferencia entre ambas fija la dispersión de referencia del ruido.

**Intento 1 y 2 (22 oct, descartados como línea base, conservados como intentos).** Con RTF 2 la
mayoría de rondas salieron `clean=0`: la carga del Mac estaba en 7–9 por apps del usuario (Firefox
con vídeo, IINA, WindowServer) y por la propia interfaz. Los tiempos se inflaron a 100–180 s y
aparecieron cortes por 180 s. Quedan en `rounds.jsonl`; no se usan para comparar.

**Decisión:** la línea base se corre a **RTF 1** (el control va por reloj de simulación, así que el
resultado no cambia; solo hay más tiempo real por ciclo) y la puerta de carga queda en 8 porque la
interfaz del Mac mantiene la media alta incluso sin simulación. La limpieza se decide ronda a ronda
con los ticks y el desfase de los escaneos, no con la carga media.

**Set A (`obs-base-a`): terminado (10 campos, 22 oct 2026).** Solo se cuentan las rondas
limpias; los intentos contaminados quedan en `rounds.jsonl`. Puntos ya re-auditados con el umbral
de deriva corregido (ver más abajo).

| Semilla-sentido | Puntos | Tiempo sim (s) | Válida | Margen | Fallos |
|---|---|---|---|---|---|
| reg0-ccw | 40 | 77,65 | no | 1,3 cm | `no_contacts` |
| reg0-cw | 40 | 85,57 | no | 0,1 cm | `no_contacts, min_wall_clearance_m` |
| reg1-ccw | 40 | 69,85 | no | 0,3 cm | `no_contacts, min_wall_clearance_m` |
| reg1-cw | 40 | 87,68 | **sí** | 2,6 cm | — |
| reg2-ccw | 40 | 109,07 | no | 1,0 cm | `no_contacts` |
| reg2-cw | 6 | 55,94 | no | 3,3 cm | fin por `wrong_side` (sign_red_2) |
| reg3-ccw | 40 | 165,38 | no | 0,9 cm | `no_contacts, min_pillar_clearance_m` |
| reg3-cw | 4 | 46,90 | no | 3,8 cm | fin por `wrong_side` (sign_red_1) |
| reg4-ccw | 40 | 83,27 | **sí** | 4,0 cm | — |
| reg4-cw | 40 | 85,47 | no | 0,3 cm | `no_contacts, min_wall_clearance_m` |

**Set B (`obs-base-b`): terminado.** Mismo set, misma puerta de calidad.

| Semilla-sentido | Puntos | Tiempo sim (s) | Válida | Margen | Fallos |
|---|---|---|---|---|---|
| reg0-ccw | 40 | 78,47 | **sí** | 1,5 cm | — |
| reg0-cw | 40 | 120,07 | no | 0,0 cm | `no_contacts, min_wall_clearance_m` |
| reg1-ccw | 40 | 66,28 | no | 1,3 cm | `no_contacts` |
| reg1-cw | 40 | 75,77 | no | 1,3 cm | `no_contacts` |
| reg2-ccw | 40 | 111,87 | no | 0,8 cm | `no_contacts, min_wall_clearance_m` |
| reg2-cw | 40 | 133,38 | **sí** | 2,7 cm | — |
| reg3-ccw | 40 | 122,16 | no | 0,8 cm | `no_contacts, min_pillar_clearance_m` |
| reg3-cw | 40 | 121,87 | **sí** | 1,6 cm | — |
| reg4-ccw | 40 | 83,67 | **sí** | 4,1 cm | — |
| reg4-cw | 40 | 87,47 | no | 0,0 cm | `no_contacts, min_wall_clearance_m` |

**Línea base del coche medido: A 2/10 válidas, B 4/10.** Los dos sets solo coinciden en `reg4-ccw`;
el ruido cambia puntos, tiempos y el desenlace de casi todos los campos. Los fallos limpios son:

1. **Contactos de micras** (12 de 20 rondas): ruedas contra muros interiores y pilares, con
   penetraciones de 0,03–0,15 mm. `no_contacts` es binario y tumba la ronda.
2. **Fin por lado equivocado** en `reg2-cw` y `reg3-cw` de A (4–6 puntos): el fallo más grave y el
   que el v2 debe resolver.
3. **Márgenes de 0,0–1,3 cm** en las rondas con contacto; las válidas quedan en 1,5–4,1 cm.

Tiempos: las válidas van de 78,5 a 133,4 s. La dispersión entre sets es enorme (`reg2-cw`: 55,9 s
cortada por falta en A frente a 133,4 s válida en B; `reg3-cw`: 46,9 s frente a 121,9 s). Con dos
sets por campo la horquilla de referencia es ancha y el criterio de tiempo solo se puede aplicar a
los campos donde ambos sets son válidos.

### Decisión: umbral de deriva de la parada (22 oct 2026)

`obstacle_full_round_report.py` exigía `drift < 0.002 m` (2 mm) además de 30 s parado en el sector
de salida. El coche medido deriva 2,5 mm y perdía los 3 puntos de la parada en 8 de 20 rondas, con
lo que `rule_maximum` las invalidaba aunque el juez de reglas las aceptaba. Decisión del usuario:
**alinear con el reglamento, `drift < 0.02 m`**. Se re-auditaron **solo** los 20 intentos
`obs-base-*`; las rondas históricas conservan su informe original. Los valores previos (37 puntos)
quedan en el historial de git y en la tabla de arriba, ya corregida.


### Por qué se falla el lado (análisis de `reg3-cw`)

En `reg3-cw` el mapa **sí** conocía el color: `sign_red_1` estaba en la lista como `red` desde el
principio. El coche cruzó su línea radial a 46,9 s con lateral +0,32…+0,44 m, es decir, **por el
lado exterior** (y=1,29 m, pared exterior a 1,5 m), cuando el rojo exige pasarlo por la izquierda.
No fue una duda de color ni un atraso: el planificador no desplazó la trayectoria hacia dentro a
tiempo (la ventana de `plan_side_window` son 0,9 m antes de la línea y el coche venía de la curva).

Consecuencia para el v2: el lado no puede decidirse «al acercarse»; hay que fijarlo al **ver** el
pilar y mantener el desplazamiento lateral hasta pasarlo, también al salir de una curva.

### Hallazgo de banco: umbral de deriva de la parada

`obstacle_full_round_report.py` calculaba `stop_valid` con `drift < 0.002 m` (2 mm) además de exigir
30 s y estar en el sector de salida. El reglamento solo pide detenerse en el sector; la deriva de
2,5 mm es ruido de simulación. Decisión del usuario (22 oct 2026): **umbral a 2 cm**, re-auditoría
solo de `obs-base-*` y rondas históricas intactas. Ver «Decisión: umbral de deriva» arriba.



### Roces de ruedas en esquinas (hallazgo preliminar)

En las rondas limpias del intento descartado, los fallos `no_contacts` no eran solo del atraso:

| Ronda | Primer contacto | Pieza | Profundidad |
|---|---|---|---|
| reg1-ccw | 36,7 s | rueda delantera izquierda, esquinas interiores oeste y norte | 0,05 mm |
| reg2-ccw | 41,0 s | rueda trasera izquierda, muro interior | 0,07 mm |
| reg3-ccw | 54,0 s | rueda trasera derecha, pilar | 0,03 mm |
| reg1-cw | 52,7 s | ruedas derechas, muro interior | 0,15 mm |

Son roces de micras, pero `no_contacts` es binario. Con el coche medido (233 mm de largo, vías
133,5/123,5 mm) el margen de planificación (3 cm muro / 4 cm pilar) no cubre el recorte de la
persecución pura en las esquinas. El v2 debe dejar más margen efectivo o recortar menos.

**Patrón de los contactos (20 rondas de la línea base):**

| Pieza | Entradas | Contra |
|---|---|---|
| Rueda delantera derecha | 58 | muro interior |
| Rueda trasera izquierda | 54 | muro interior |
| Rueda trasera derecha | 54 | muro interior |
| Rueda delantera izquierda | 40 | muro interior |
| Chasis (`base_footprint`) | 12 | muro exterior |

- Dominan los **muros interiores** (202 de 218 entradas; 12 contra pilares y 4 contra el muro
  exterior). Es el recorte de la trazada en las esquinas, no un choque frontal.
- Las entradas se repiten por episodio: el primer contacto de cada ronda suele ser una **rueda
  trasera** en la salida de una curva o durante `PLAN_BLOCKED`/recuperación.
- Profundidades de 0,003–0,17 mm: el coche pasa rozando, no choca.
- El modelo de huella usa `REAR_L = 0,0852 m`, pero la rueda trasera llega a 0,0892 m (radio
  0,0305 desde el eje a −0,0587): 4 mm fuera del rectángulo que comprueba el planificador. Con el
  error de localización (~1 cm) y el retardo del servo, un margen de 3 cm se queda en cero.



## Fase 1 · Investigación (hallazgos preliminares)

### Mapa de módulos de la estrategia actual

| Módulo | Entradas | Qué decide | Salida |
|---|---|---|---|
| `obstacle_mission.py` | escaneo, IMU, imagen, distancia | `CALIBRATE` → `DETECT_DIRECTION` (ajuste de muros CCW/CW, cámara de respaldo) → driver; rama de aparcamiento | `(speed, steer, state)` |
| `obstacle_localizer.py` | puntos LiDAR | pose `(x, y, θ)` por mínimos cuadrados contra los muros conocidos (ganancia 0,5), predicción por distancia + rumbo del giroscopio; `initialize` global al arrancar; `direction_from_scan` compara inliers CCW/CW | pose, inliers, RMS |
| `obstacle_seat_map.py` | clústeres LiDAR + observaciones de cámara | 24 asientos reglamentarios; el LiDAR localiza, la cámara vota color; agrupa las dos filas de cada hueco | lista de pilares `{x, y, color, t, n}` |
| `obstacle_perception.py` | escaneo, imagen | clústeres cortos (0,015–0,12 m, hasta 2,5 m), manchas HSV rojo/verde, asociación por rumbo (±0,12 rad), líneas naranja/azul para el sentido | clústeres, bloques, dirección |
| `obstacle_beam_planner.py` | pose, mapa, φ, φ_goal | haz de 9 volantes × 22 pasos de 0,08 m (beam 60, celda 0,05 m) con costes de muro, pilar, lado, vista, volante, tasa y rumbo final; regla del lado también al atravesar la línea radial | trayectoria `(x, y, θ, δ)` |
| `obstacle_driver.py` | pose, mapa, trayectoria | replanifica cada 0,1 s; persecución pura (lookahead 0,16 + 0,25·v); velocidad por curvatura y frenada; `PLAN_RECOVER` con arcos de marcha atrás puntuados; `PLAN_BLOCKED` tras 1 s sin camino; `FINISH` a 1,5 unidades y `DONE` al llegar | `(speed, steer, state)` |
| `obstacle_field.py` | — | geometría del campo y del coche (muros, isla, asientos, marcos CCW/CW) | constantes y utilidades |

Observaciones para el diseño:

- **Todo el control pasa por el mapa**: sin mapa de asientos ni planificador no hay lado ni trayectoria.
- `plan_latency` vale 0 en el perfil activo, así que la rama de *feedforward* de latencia
  (`plan_feedback`, `plan_latency`) **no se ejecuta** hoy; es candidata a eliminar (H-O5).
- Los 48 campos de `ObstacleConfig` se leen en algún sitio, pero 32 son fijos y nunca se han
  ajustado por perfil. Los parámetros realmente usados en pista son los 16 de ROS.
- La cámara solo aporta **color** (y el respaldo de sentido); el dónde lo pone el LiDAR. Eso hace
  plausible H-O1/H-O2 (basta el próximo pilar, no los 24 asientos), pero hay que medirlo.

### Rondas ya grabadas (50 rondas sin aparcamiento, hasta el 21 oct 2026)

- **28/50 válidas**; **46/50 con 40 puntos estimados**.
- Los fallos son casi todos de **margen**: muro exterior/interior (11 rondas), pilar (8), ambos (2);
  2 con contactos y 2 por debajo del máximo de puntos.
- Tiempo desde Start: media **79,3 s**, mediana **73,8 s**, rango 56,6–180 s.
- **184 episodios de recuperación** (`PLAN_RECOVER`) en 36 de las 50 rondas, y 275 entradas en
  `PLAN_BLOCKED`.

### Presupuesto de fases en el set `os1` (10 rondas)

| Ronda | Tiempo | PLAN | PLAN_RECOVER | PLAN_BLOCKED | FINISH | DONE (parada) | Margen |
|---|---|---|---|---|---|---|---|
| reg0-ccw | 75,1 | 66,0 | 1,9 (1) | 1,3 | 4,8 | 31,9 | 1,8 cm |
| reg0-cw | 68,1 | 61,5 | 0 | 0 | 5,6 | 31,9 | 0,8 cm |
| reg1-ccw | 97,0 | 51,6 | 10,4 (5) | 5,7 | 28,2 | 31,9 | 0,3 cm |
| reg1-cw | 62,6 | 57,8 | 0 | 0 | 3,8 | 31,9 | 2,3 cm |
| reg2-ccw | 66,2 | 56,9 | 2,8 (2) | 2,3 | 3,1 | 31,9 | 0,4 cm |
| reg2-cw | 64,8 | 56,0 | 1,9 (1) | 1,1 | 4,8 | 31,9 | 0,5 cm |
| reg3-ccw | 77,5 | 66,0 | 3,9 (2) | 2,2 | 4,4 | 31,9 | 1,1 cm |
| reg3-cw | 76,6 | 65,5 | 3,8 (2) | 2,3 | 4,0 | 31,9 | 1,5 cm |
| reg4-ccw | 66,1 | 59,4 | 0 | 0 | 5,7 | 31,9 | 2,9 cm |
| reg4-cw | 70,1 | 60,7 | 1,0 (1) | 1,4 | 5,9 | 31,9 | 0,5 cm |

Lectura preliminar: el tiempo de conducción (`PLAN`) es 52–66 s; la parada reglamentaria fija
31,9 s en todas; `reg1-ccw` se desvía (10,4 s de recuperación y 28,2 s en `FINISH`). El margen,
no el tiempo, es el problema: 8 de 10 rondas quedan por debajo de 2 cm.

### Ablaciones en Gazebo (22 oct 2026)

Método: 4 rondas por pieza (`reg0-ccw`, `reg1-cw`, `reg2-ccw`, `reg3-cw`), RTF 1, puerta de carga 4,
sin GUI. `tools/obstacle_param_ablation.sh abl1`.

| Pieza | reg0-ccw | reg1-cw | reg2-ccw | reg3-cw |
|---|---|---|---|---|
| `base` | 40, 78,4 s, contacto | **40, 75,5 s, válida** | 3, 21,9 s, pilar fuera | 14, 40,6 s, pilar fuera |
| `marginsup` (5/6/7 cm) | 22, 102,6 s, contacto | **40, 84,9 s, válida** (3,2 cm) | 5, 180 s, contacto | 14, 95,0 s, pilar fuera |
| `speed035` (0,35 m/s) | 40, 83,5 s, contacto | 40, 89,3 s, contacto | **40, 84,3 s, contacto** | 6, 53,9 s, `wrong_side` |

Conclusiones de la fase 1:

1. **Los márgenes del planificador no son la palanca.** Subirlos a 5/6/7 cm deja 3 de 4 rondas con
   contacto y empeora puntos y tiempos. Los roces ocurren igual con 1,3–1,6 cm de margen real.
2. **Bajar a 0,35 m/s evita el empuje grave de pilares**: `reg2-ccw` pasa de 3 puntos (pilar fuera)
   a 40 puntos, aunque sigue rozando el muro interior. Es la única ablación con efecto claro.
3. **El fallo de lado es independiente de la velocidad**: `reg3-cw` termina en `wrong_side`
   (sign_red_2) a los 54 s también a 0,35 m/s.
4. **Los contactos son de rueda delantera contra el muro interior** en la salida de curva (primer
   contacto a 38–73 s), con 0,002–0,17 mm de penetración. No es el planificador: es el seguimiento
   (error de localización + retardo del servo) recortando la trazada.

**Pilares fuera de su círculo (regla 9.24.6).** En `base` `reg2-ccw` (sign_green_3) y `reg3-cw`
(sign_red_1) el coche **empujó** el pilar 9,1 y 13,9 mm con 235 y 1006 mensajes de contacto, hasta
sacarlo del círculo. No es un roce: es apoyo sostenido. Son las mismas semillas que en la línea base
acabaron en `wrong_side`: el planificador lleva al coche al lado equivocado y ahí empuja.

Implicaciones para el diseño del v2: decidir el lado **al ver** el pilar y mantenerlo; no confiar en
el margen de planificación sino en una **trayectoria desplazada** y un seguimiento más lento; y
limitar la velocidad (≈0,35 m/s) hasta demostrar que se puede subir sin empujar pilares.

*(Pendiente: ablaciones de valores fijos —`loc_gain`, `side_cost`, `view_gain`, `beam`, `recover`—
que requieren una rama aparte.)*

### Hallazgo de banco: el juez usa el contorno viejo del coche
`obstacle_audit_geometry.collision_polygons` construye el coche con las medidas **anteriores**:
chasis de 177×90 mm (semilados 0,0885/0,045), ruedas a ±65 mm del centro y vía ±50 mm. El coche
medido (`vehicle.py`) mide 233 mm de largo (0,1477 delante / 0,0852 detrás), 148 mm de ancho y tiene
la vía delantera a 133,5 mm. El juez calcula con un coche **más pequeño** que el real, así que sus
márgenes y su intervalo lateral en la línea del pilar son optimistas. Los contactos reales los
detectan los sensores de Gazebo, no este cálculo.

No se corrige dentro de este trabajo (plan §5, fase 1.6): cambiar el contorno obliga a re-auditar
todas las rondas históricas. Se anota como límite del banco y el laboratorio del v2 usará el
contorno medido para su propio cálculo de contactos y márgenes.


## Fase 2 · Laboratorio del Obstacle (`obstacle_lab`)

Primera versión: `src/robotek_evaluation/robotek_evaluation/obstacle_lab.py`, con pruebas en
`src/robotek_evaluation/test/test_obstacle_lab.py` (4 pasan).

Qué reutiliza de una ronda grabada: su `world.sdf` (muros y pilares) y su `manifest.json`
(posición, color y lado de cada pilar). Qué simula: rayos LiDAR contra muros y pilares (10 Hz,
306 rayos, ruido y pérdidas), giroscopio a 50 Hz, cámara a 6 fps que entrega **observaciones**
(rumbo y color) de los pilares a menos de 2 m y con la imagen a ≤ 0,15 s del escaneo, actuadores
del coche real (`open_lab.Actuators`) y la estrategia actual cableada como su nodo (odometría
LiDAR para la distancia, giroscopio integrado para el rumbo). El juez es el de Gazebo
(`summarize_full`): el laboratorio escribe una ronda temporal (telemetría a 10 Hz, eventos,
contactos y verdad de pilares) y la puntúa.

```bash
python3 -m robotek_evaluation.obstacle_lab --run docs/obstacle-challenge-runs/<ronda> --compare
```

### Fidelidad medida (22 oct 2026)

| Ronda | Gazebo | Laboratorio | ¿Coincide? |
|---|---|---|---|
| `reg4-ccw` | 40 pts, 83,27 s, válida | 40 pts, 81,50 s, válida (margen 0,9 cm) | **sí** (tiempo −2,1 %) |
| `reg0-ccw` | contacto a 19,4 s (sigue y termina) | contacto a 18,7 s | **casi** (−0,7 s) |
| `reg1-cw` | 40 pts, 87,68 s, válida | contacto a 18,8 s | **no** (contacto falso) |

La trayectoria coincide en los primeros segundos (mismo giro a la izquierda al salir, mismas
posiciones ±5 cm a los 2,8 s), pero con márgenes reales de ~4 cm esa diferencia decide si hay
contacto. La cámara es la parte menos fiable: el laboratorio da el color directamente y la
asociación real depende de píxeles, oclusión y del cuadro.

### Límites (declarados, no ocultados)

- **Filtro de un solo sentido**: fallar aquí es mala señal; pasar aquí no demuestra nada.
- No modela deslizamiento, el plugin Ackermann, imágenes, oclusión, fuerzas de contacto ni el
  movimiento de pilares. Un contacto termina la ronda (como en el laboratorio del Open).
- El juez sigue usando el contorno viejo del coche; el laboratorio mide contactos y márgenes con
  el contorno medido, así que sus dos números no son comparables entre sí.
- Con 3 rondas de contraste no se puede afirmar fidelidad de ±2 cm / ±5 %; hoy **no se usa para
  decidir** puntos ni validez, solo para comparar variantes entre sí y detectar fallos gruesos.

## Fase 3 · Diseño del v2 (propuesta para aprobar)

Objetivo: 3 vueltas sin tocar nada, con el **mínimo** de estados, parámetros y líneas, y sin ser
peor que la línea base (2–4/10 válidas). Se apoya en lo medido: los márgenes del planificador no
evitan los roces; la velocidad sí evita empujar pilares; el lado debe fijarse al ver el pilar.

### Idea

Conducir el corredor por **distancia al muro interior** (la isla siempre queda a un lado), con un
**desplazamiento lateral** que se fija al ver el próximo pilar según su color y se mantiene hasta
pasarlo. Nada de mapa de 24 asientos ni de haz de trayectorias.

- **SETUP**: calibrar el giroscopio (0,3 s) y decidir el sentido con el ajuste de muros del primer
  escaneo (se conserva `direction_from_scan`, 20 líneas).
- **RUN**: error de rumbo + error lateral contra la distancia interior objetivo; velocidad 0,35 m/s
  (0,25 cerca de un pilar sin color). Si no hay camino (muro de frente), retroceder 0,15 m una vez.
- **STOP**: al llegar a 24 unidades de pista (3 vueltas) y al sector de salida, frenar y mantener
  30 s. Tres estados, un `stop_reason` como dato.

### Contrato de datos

La decisión recibe por ciclo una **observación inmutable** de 7 campos:

| Campo | Origen |
|---|---|
| `inner` / `outer` | distancia mediana a los muros laterales (±90°) |
| `front` | distancia mínima al frente (±20°) |
| `heading_error` | rumbo del coche menos la tangente del carril (muros o giroscopio) |
| `progress` | unidades de pista desde Start (localizador de muros) |
| `pillar` | `(lateral, distancia, color)` del próximo pilar a ≤1,2 m; color `None` si no se ha visto |
| `direction` | `ccw`/`cw` (una vez, en SETUP) |

Devuelve `(speed, steer)`.

### Qué se conserva y qué se quita

| Pieza actual | Líneas | Decisión | Motivo |
|---|---|---|---|
| `obstacle_localizer.py` | 72 | **se conserva** | pose y progreso con error ~1 cm; 3 vueltas sin él no son fiables |
| `direction_from_scan` | 20 | **se conserva** | decide el sentido en el primer escaneo |
| `scan_clusters` | 33 | **se conserva** | es el «dónde» del pilar |
| `color_blocks` + `associate` | 70 | **se conserva, simplificado** | el color es el «por dónde»; se asocia al pilar más cercano |
| `obstacle_seat_map.py` | 42 | **se quita** | H-O2: basta el próximo pilar; los 24 asientos no aportan al lado |
| `obstacle_beam_planner.py` | 122 | **se quita** | H-O3: la trayectoria es un desplazamiento lateral, no una búsqueda |
| `obstacle_driver.py` | 179 | **se sustituye** | control lateral + velocidad, sin persecución sobre haz |
| `obstacle_mission.py` | 120 | **se sustituye** | 3 estados en vez de 6 |
| `plan_latency`/`plan_feedback` | — | **se quita** | la rama no se ejecuta hoy (latencia 0) |

### Tamaño objetivo (mismo método, `tools/code_metrics.py`)

| Métrica | Actual (sin nodos) | v2 objetivo |
|---|---|---|
| Líneas decisión + percepción | 723 | **≤ 360** |
| Complejidad total | 227 | **≤ 110** |
| Función más compleja | 15 | **≤ 10** |
| Estados | 6 | **3** |
| Campos de observación | — | **7** |
| Parámetros ROS | 16 | **≤ 12** |

Parámetros propuestos (12): `cruise_speed` 0,35, `pillar_speed` 0,25, `finish_speed` 0,15,
`inner_distance` 0,50, `pillar_clearance` 0,18, `pillar_lookahead` 1,20, `steer_kp` 1,8,
`steer_kd` 0,2, `steer_limit` 0,279, `stop_progress` 23,7, `scan_max_age` 0,35, `imu_max_age` 0,20.
Calibración, timeout de sentido y umbrales de color quedan como constantes.

### Hipótesis y plan B

| # | Hipótesis | Experimento | Si falla |
|---|---|---|---|
| H-V1 | Seguir el muro interior a 0,5 m completa las 3 vueltas sin haz | laboratorio + set de Gazebo | volver al planificador reducido (pocas trayectorias) |
| H-V2 | Fijar el lado al ver el pilar elimina los `wrong_side` de `reg2`/`reg3` | esas dos semillas primero | conservar el mapa de asientos |
| H-V3 | 0,35 m/s evita empujar pilares y aun así baja de ~100 s | set de Gazebo | 0,30 m/s y aceptar más tiempo |
| H-V4 | El desplazamiento lateral de 0,18 m basta para no rozar | margen mínimo ≥ 2 cm en 10 rondas | 0,22 m y mirar el tiempo |

### Límites declarados

- **Sin aparcamiento** (proyecto aparte) y **sin recuperación de atascos** más allá de un retroceso
  de 0,15 m.
- No usa pose de Gazebo, ni odometría de ruedas, ni estado de los pilares: LiDAR, giroscopio y
  cámara, como hoy.
- El objetivo es **no ser peor** que la línea base (2–4/10 válidas) y bajar los contactos; el
  tiempo queda en segundo plano.

### Criterios de aceptación

1. 10/10 rondas limpias en Gazebo con **≥ 4 válidas** (mejor que la mejor línea base) y 40 puntos.
2. Sin contactos ni `wrong_side` en las 10; margen mínimo ≥ 1 cm, idealmente ≥ 2 cm.
3. Tiempo medio ≤ 110 s (la línea base válida va de 78 a 133 s).
4. Tamaño dentro de la tabla de arriba y pruebas de capa 1 pasando.
5. `strategy:=v2` seleccionable; el valor por defecto **no cambia**.

## Fase 4 · Implementación del v2 (en curso)

Código en `src/robotek_obstacle/robotek_obstacle/v2/`:

| Archivo | Líneas | Complejidad | Qué hace |
|---|---|---|---|
| `scene.py` | 50 | 11 | observación inmutable y geometría del carril (`lane_pose`, `lane_normal`, `advance`) |
| `settings.py` | 23 | 6 | 11 parámetros y validación |
| `mission.py` | 226 | 81 | `SETUP → RUN → STOP`, control de carril, lado por pilar, retroceso de 0,15 m |
| **Total** | **299** | **98** | máximo por función **9**; objetivo ≤ 360, ≤ 110 y ≤ 10: **cumplido** |

Pruebas: **75 pasan** en `robotek_obstacle` y `robotek_evaluation`.

Estado sobre `reg4-ccw`: **5/5 semillas válidas**, 40 puntos, 106,70–107,30 s y margen medido
4,4–6,7 cm. La semilla 0 ya no roza el primer pilar.

Diagnóstico corregido de la semilla 0: el primer escaneo solo contenía un pilar verde lejano
(progreso 2,01). El v2 fijaba ese latch y descartaba el verde cercano (progreso 1,01) cuando
aparecía en el escaneo siguiente. El fallo no era solo cinético. Un latch ahora puede reemplazarse
por otro candidato que esté al menos `PILLAR_SWITCH = 0,25` unidades de pista más cerca; el ruido
menor del mismo pilar lo conserva. No hace falta pre-posicionar en `SETUP`.

Lo que se corrigió durante la implementación:

- **El lado se mide en el sistema de la recta del pilar**, no en el del coche: en la salida de una
  curva el sistema gira y el desplazamiento salía mal.
- Los asientos están a **±0,1 m del centro del carril**, así que el lateral se redondea a esa fila;
  el carril central pasa a 0,1 m del pilar y **siempre** hay que desplazarse.
- El latch puede cambiar a un pilar claramente más cercano y añadimos pruebas para separar ese caso
  de la oscilación de distancia del mismo pilar.
- En CW se espejan la coordenada lateral del clúster, el volante y el color (`red`/`green`) como en
  la estrategia actual.
- `pillar_clearance` 0,18 m y 0,30 m/s cerca de pilares: con menos margen el seguimiento (±5 cm)
  roza; con menos velocidad el coche no puede cambiar de lado a tiempo (0,15 m/s daba 131 s y
  roces).

### Hallazgo: la anchura del coche en la estrategia actual

`obstacle_field` importa `HALF_WIDTH` de `vehicle.py`, que es **0,045 m** (media placa de chasis),
cuando el contorno medido es `OUTLINE_HALF_WIDTH` = **0,074 m**. La estrategia actual (y el juez,
que usa 0,045) creen el coche **58 mm más estrecho** de lo que es. Eso explica que los márgenes de
3–4 cm no evitasen los roces. El v2 usa el ancho medido (0,074); la estrategia actual se deja igual
para no invalidar las comparaciones históricas.

### Set completo de laboratorio: 3/10

Cada campo se ejecutó sobre su ronda más reciente de `obs-base-a`, con el mismo número de semilla
de layout.

| Campo | Puntos | Tiempo sim (s) | Válida | Margen | Fallo |
|---|---:|---:|---|---:|---|
| reg0-ccw | 40 | 97,50 | **sí** | 4,0 cm | — |
| reg0-cw | 1 | 6,60 | no | 0,0 cm | contacto con `sign_green_1` |
| reg1-ccw | 40 | 87,20 | **sí** | 5,1 cm | — |
| reg1-cw | 6 | 28,20 | no | 1,3 cm | `wrong_side`: `sign_red_1` |
| reg2-ccw | 4 | 16,00 | no | 3,2 cm | `wrong_side`: `sign_green_3` |
| reg2-cw | 0 | 1,00 | no | 0,0 cm | contacto con `sign_green_1` |
| reg3-ccw | 4 | 17,70 | no | 5,9 cm | `wrong_side`: `sign_green_2` |
| reg3-cw | 4 | 17,30 | no | 5,4 cm | `wrong_side`: `sign_red_1` |
| reg4-ccw | 40 | 107,00 | **sí** | 4,7 cm | — |
| reg4-cw | 4 | 13,00 | no | 0,0 cm | contacto con `sign_red_2` |

Al comparar resultados anteriores: espejar correctamente CW eliminó el fallo inmediato de lado,
pero no los contactos. Frenar más, separar menos y cambiar el FOV del laboratorio al valor medido
de 66,7° no resolvieron los fallos. Reducir `pillar_clearance` por debajo de 0,18 m tampoco.

### Límites que quedan

1. **Secuencias opuestas en una esquina.** `reg2/3-ccw` y varias CW exigen pasar un pilar interior y
   otro exterior casi consecutivos. Una única curva de carril desplazado llega al segundo con el
   coche todavía en el lado del primero. Hace falta un waypoint de paso o una maniobra explícita de
   entrada/salida de esquina.
2. **Color tardío.** En algunos campos la cámara entrega el color cuando el centro del coche está a
   ~0,1 m lateral del pilar. No queda recorrido para alcanzar el offset de 0,254 m. Apartarse más,
   mantener el carril, frenar o el FOV medido no lo corrigieron en las pruebas.
3. **La fase 4 no está cerrada** porque el criterio de 10/10 no se cumple; la fase 5 no debe empezar
   todavía.

La siguiente iteración debe atacar primero la secuencia de esquina con un prototipo mínimo en el
laboratorio, sin añadir estados ni parámetros hasta demostrar que mejora CCW y CW.

### Iteración del 25 oct 2026: bucle rápido, memoria de color, líneas de esquina y salida

**Método.** En vez de editar y repetir el set a ciegas, primero se diagnosticó cada fallo y
después se atacó cada clase con su arreglo geométrico.

- Primero se investigó en paralelo cómo funciona el laboratorio, la causa de cada uno de los 7
  fallos y el método del Open v5.
- El bucle de iteración se hizo rápido:
  - `tools/obstacle_lab_suite.py` corre campos × semillas en paralelo desde `src`. El `install/`
    estaba desactualizado y daba resultados falsos: `reg4-ccw` tocaba un pilar a los 3,4 s.
  - Genera los campos con el mismo generador del runner. Los layouts 0–4 son el set estándar;
    del 5 en adelante son un set reservado (no se ajustó con ellos).
  - `--early` corta la ronda 1,5 s después de un lado incorrecto claro, y el juez sigue
    puntuando la ronda.
  - `--tmax` recorta la ronda a una esquina.
  - Las **50 rondas** (10 campos × 5 semillas) tardan **~26 s** con 12 procesos; antes, una
    ronda costaba ~27 s de CPU.
- Commits: `f7dc73a`, `a7ffcfd`.

**Laboratorio más fiel.** La cámara del laboratorio era la idealizada (60°, centrada). Ahora es
la del coche real: 66,7°, girada 4,4° a la izquierda, como Gazebo con `real_car:=true` (`54f97d2`).
- La línea base sigue en 15/50.
- Hallazgo: en el marco espejado del CW, el lado de la isla solo ve hasta **28,9°**, contra
  37,8° en CCW. Ver una señal interior es más difícil en CW.

**Causas de los 7 fallos.** El espejado CW no tenía fallos, la ubicación de las señales coincidía
con la real y el juez marcaba bien el lado.

| Clase | Campos | Causa | Arreglo |
|---|---|---|---|
| S (salida) | `reg2-cw` | señal 0,25 m delante del coche: hacia adelante no se llega a su lado | ver y retroceder (`_start`) |
| V (color) | `reg2-ccw`, `reg3-ccw`, `reg3-cw`, `reg1-cw` | la señal interior a la salida de una esquina no entra en la cámara; el v2 no recordaba colores | memoria por asiento + desvío para verla (`_lookouts`) |
| C (esquina) | `reg0-cw`, `reg4-cw` y parte de las de clase V | desplazamiento constante en la curva (radio imposible), el seguidor cortaba la curva hacia la señal siguiente, latch liberado tarde | línea recta-arco-recta por esquina (`corner.py`) y plan lateral con rampas |

**Cambios en el v2.**
- **Memoria por asiento:** 16 asientos, con votos de color que se conservan toda la ronda.
- **Plan lateral:** el desplazamiento se mantiene ±0,15 unidades alrededor de cada señal, con
  rampas entre señales. Sustituye al latch.
- **`corner.py`:**
  - Por esquina busca `d_a`, `d_b` y el radio de una línea recta-arco-recta.
  - Comprueba el contorno medido del coche, el lado de cada señal (cortado en su línea, como el
    juez), la isla y el muro exterior.
  - Con ≥ 7 cm de margen, prefiere la línea más cercana al centro.
  - Los 24 casos de esquina tienen línea con ≥ 4,1 cm sobre el papel (hay prueba unitaria).
- **Lookahead de 0,25 m** (antes 0,35 m): con 0,35 el seguimiento cortaba las curvas unos 10 cm
  hacia dentro.
- **Color desconocido:**
  - Apartarse 0,12 m (antes 0,18), para no sacar la señal del campo de la cámara.
  - Si la señal desconocida está a la salida de la próxima esquina, la línea pasa por +0,15 m
    (lado de la isla) 1,5 unidades antes de ella.
- **Salida:** el coche se detiene 0,25 s para registrar las primeras señales.
  - Retrocede en recta si la primera señal está en el asiento central y demasiado cerca.
  - Solo en ese caso: la tarjeta de una señal deja vacío el asiento de detrás, que el LiDAR no ve.
- Commits: `ffbb3b1`, `8bf905f`.

**Resultados (laboratorio, 5 semillas por campo).**

| Campo | Línea base | Ahora | Tiempo (s) | Margen | Fallo restante |
|---|---:|---:|---:|---:|---|
| reg0-ccw | 5/5 | **5/5** | 97,8–97,9 | 1,9–2,1 cm | — |
| reg0-cw | 0/5 | 0/5 | — | — | contacto `sign_green_1` (esquina dentro→fuera, 4,1 cm sobre el papel) |
| reg1-ccw | 5/5 | **5/5** | 87,7–87,8 | 3,0–3,1 cm | — |
| reg1-cw | 0/5 | **5/5** | 107,1–107,2 | 5,4–5,5 cm | — |
| reg2-ccw | 0/5 | **4/5** | 93,5–93,7 | 1,1–1,5 cm | 1 contacto `sign_green_2` |
| reg2-cw | 0/5 | 0/5 | — | — | salida resuelta; lado incorrecto en `sign_red_1` (color) |
| reg3-ccw | 0/5 | **5/5** | 90,4–90,7 | 1,0–1,1 cm | — |
| reg3-cw | 0/5 | 0/5 | — | — | lado incorrecto en `sign_red_1` (color de la señal interior en 4,0) |
| reg4-ccw | 5/5 | **5/5** | 106,5–106,7 | 3,3–3,4 cm | — |
| reg4-cw | 0/5 | 0/5 | — | — | lado incorrecto en `sign_red_2` (señal interior central en 4,5) |
| **Total** | **15/50** | **29/50** | | | |

- **Set reservado (layouts 5–14, CCW y CW, semilla 0):** **7/20**; la versión de `ffbb3b1` daba
  4/20. Casi todos los fallos son contactos. El set estándar ya está **sobreajustado**: no se debe
  iterar más mirando solo los 10 campos.
- **Sin estabilidad:** con la parada de 0,25 s en la salida, `reg4-cw` pasa de 3/5 a 0/5, y
  `reg2-ccw` cambia de semilla fallida. Varios márgenes son de 1–2 cm.
- **Tamaño:** 513 líneas / 185 de complejidad / máximo 10 por función. **No cumple** el objetivo
  de la fase 4 (≤ 360 / ≤ 110).

**Lo que queda y cómo seguir.**
1. **Precisión del seguimiento:** el plan tiene ≥ 4 cm y el coche pasa a 1–3 cm. Medir el error
   lateral contra el plan en el laboratorio y añadir anticipación de la curvatura (feedforward) en
   vez de un lookahead más corto.
2. **Ver las señales interiores en CW** (lado de la isla limitado a 28,9°). Opciones:
   - asomarse con el coche (girar la nariz hacia la señal antes de comprometerse);
   - re-orientar la cámara del coche real a 0° (decisión del equipo);
   - aceptar perder la primera vuelta en esos casos.
3. Medir siempre con el set reservado (`--layouts 5-24`) además del estándar.
