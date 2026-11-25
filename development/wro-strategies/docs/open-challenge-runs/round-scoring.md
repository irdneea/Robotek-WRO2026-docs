# Puntos y tiempos por ronda — Open Challenge

Instrucción persistente del usuario: guardar puntos y tiempos por ronda en cada
prueba, también cuando falle o quede incompleta.

Una **vuelta** recorre ocho secciones. Una **ronda** es un intento de tres vueltas,
con límite de 180 segundos. El reloj empieza al pulsar **Start**: incluye la
calibración y la detección de dirección que ocurran después (§9.13).

El máximo del Open es **30 puntos** (§10.2 y tabla de puntuación):

| Concepto | Puntos máximos |
|---|---:|
| Salir de secciones en el sentido de la ronda | 24 |
| Completar vueltas de ocho secciones | 3 |
| Detenerse en la sección de llegada después de tres vueltas | 3 |

La mejor ronda se elige por puntos. Si los dos intentos del equipo tienen los
mismos puntos, se elige el menor **tiempo total de ronda** (§10.5). No se elige
por la vuelta más rápida. Por ejemplo, 30 puntos en 40 s superan a 27 puntos en
22 s; entre dos rondas de 30 puntos, 22 s superan a 30 s.

Esto describe la selección de la mejor ronda Open; la clasificación general
suma Open, Obstacle y documentación y tiene sus propios desempates (§10.7–10.8).

Fuente local: [Reglas generales 2026](../WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md),
§9.13, §9.24, §10 y apéndice A (evaluación de parada de al menos 30 segundos).

## Registro automático

`run_gui_experiment.sh` guarda por ejecución:

- `events.jsonl`: Start aceptado y entrada a DONE, con ambos relojes. Distingue
  Start por tópico de Start automático al recibir el primer escaneo.
- `round.json` y el campo `round` de `summary.json`: puntos estimados y desglose,
  estado del intento, tiempos desde Start, tiempos de movimiento y parciales.
- `docs/open-challenge-runs/rounds.jsonl`: registro acumulado por ejecución.
  Recalcular un registro actualiza esa entrada sin duplicarla.
- Telemetría, sensores, imágenes, configuración y logs del ejecutor existente.

Si el intento acaba sin DONE, se registra el tiempo hasta la última muestra
como intento incompleto; no se presenta como final reglamentario. Un fallo sin
telemetría conserva un registro con datos desconocidos, sin inventar puntos.

Los puntos son una **estimación de simulación**, no una decisión de jueces:
el progreso angular de ground truth aproxima secciones y vueltas; una misión
completa validada geométricamente permite estimar 24 + 3 y un bonus provisional
de 3. En intentos parciales, los límites angulares no equivalen exactamente a
salir de cada sección con todo el vehículo. No se juzgan automáticamente
contactos, desplazamiento de paredes, reparaciones humanas ni legalidad del
inicio. DONE tampoco certifica la parada de 30 segundos. `points_official`
permanece desconocido hasta una evaluación reglamentaria.

Los registros históricos carecen de eventos Start. Sus tiempos desde Start se
guardan como desconocidos; los tiempos de movimiento originales se conservan.
La suma de parciales tampoco incluye necesariamente el tramo final de parada.

## Paredes y contacto (§9.18, §9.23, §9.24)

- **Mover un muro** (interior o exterior): prohibido → se detiene el vehículo,
  **0 puntos y tiempo máximo** en la ronda.
- **Tocar/golpear un muro sin moverlo**: permitido, se continúa **sin penalización**.
- **Muro exterior en Open Challenge: no se puede tocar** (§9.18). Sin penalización
  explícita; decide el juez y §9.26 tiende al **peor resultado**.
- **Golpear y quedar detenido**: se puede pedir **reparación** (1 vez/ronda, el
  reloj no se detiene; no tras empezar la 3ª vuelta; prohibido subir programas o
  datos). Violar esas condiciones → descalificado de la ronda (0 pts, tiempo máx).
- **Salir de la pista (moviendo el muro) o del campo**, o **dañar** el campo o un
  elemento del juego: termina la ronda (§9.24.12–13).

No es automático perder por rozar un muro interior; sí lo es mover cualquier muro.
Por eso la telemetría guarda `min_outer_body_clearance_m` y
`min_inner_body_clearance_m`: verifican que nunca se tocó el exterior.
