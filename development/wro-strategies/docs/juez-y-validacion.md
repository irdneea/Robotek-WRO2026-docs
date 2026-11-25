# Juez de reglas y validación estándar

Fecha: 6 de octubre de 2026. Código: `src/robotek_evaluation/robotek_evaluation/rule_judge.py`.

Los puntos **oficiales** solo los da un juez sobre el robot real. En simulación separamos
dos preguntas que antes estaban mezcladas:

1. **`rule_judge`**: qué otorgaría el reglamento, aplicado a la telemetría con la pose de
   Gazebo (solo auditoría, nunca control). Sigue siendo simulación.
2. **`validation`**: si la ronda cumple nuestro criterio interno de aceptación (seguridad y
   repetibilidad). Mismo formato y umbrales para Open y Obstacle.

Ambos bloques quedan en cada `round.json`, en `rule_judge.json` (Open) y en `rounds.jsonl`.

## Juez de reglas — Open (v2, 8 de octubre)

Para juzgar la huella se prefiere `audit_pose.csv`, grabado aparte a 50 Hz.
La estrategia sigue usando exclusivamente sensores; nunca recibe esa pose.
La telemetría a 10 Hz puede omitir una esquina atravesada completamente
durante solo 40 ms. Se conserva como respaldo para rondas sin auditoría completa.
`pose_source` y `pose_sample_count` identifican la evidencia usada; Start y DONE
siguen viniendo de sus eventos exactos. Se mantienen las mismas reglas,
umbrales y comprobaciones de contacto y parada.

En la serie `realcar-symmetric-*` se recalcularon **todas** las rondas bajo este
criterio, incluyendo las fallidas y los dos perfiles del set estándar. Los
informes anteriores permanecen como `round-judge-v1.json` y `rule_judge-judge-v1.json`;
el [historial](open-challenge-runs/realcar-open-history.md) explica las diferencias.

| Regla | Cómo se juzga |
|---|---|
| 1.1 secciones (1 pt, máx. 24) | Secciones fijas del tapete (curvas = cuadrados de las esquinas). Cuenta cuando la **huella completa** (chasis + ruedas con su ángulo medido) pasa entera a la sección siguiente en el sentido de la ronda. Volver por una frontera ya cruzada no suma. |
| 1.2 vueltas (1 pt, máx. 3) | Cada 8 secciones; la vuelta se completa al salir entero de la última curva. |
| 1.3 parada (3 pts) | Tras 3 vueltas: huella entera dentro de la sección de salida, quieto ≥ 15 s (nota 2 de 9.24.2) con deriva ≤ 2 mm. Si la telemetría termina antes, usa `stop-observation.json`. |
| 9.24.3 fin de ronda | Pasarse entero a la curva siguiente tras 3 vueltas (sin parada), o cruzar dos fronteras en sentido contrario (Apéndice A §4). |
| 9.24.1 tiempo | 180 s desde Start. |
| 9.18 muro exterior | Prohibido tocarlo en el Open, pero la regla **no dice la consecuencia**: se marca como falta y no se descuenta. Con sensor: contacto real; sin sensor (rondas viejas): "probable" si la huella muestreada queda a ≤ 8 mm. |
| Muros interiores | Tocarlos está permitido si no se mueven (en simulación son fijos). |

Tiempo: Start → fin de ronda (evento `done` si existe, si no el inicio de la parada).

## Juez de reglas — Obstacle (sin aparcar)

Ya estaba basado en reglas (`obstacle_full_round_report.py`): secciones, vueltas, parada,
bonus de señales 1.4–1.7, lado de paso por la línea radial (9.24.5) y pilar fuera del círculo
de 85 mm (9.24.6). Ahora se expone con el mismo bloque `rule_judge` (máximo 40 en este
alcance; 62 con aparcamiento, no evaluado).

## Validación estándar (v1)

| Chequeo | Umbral |
|---|---|
| `rule_maximum` | puntos por reglas = máximo (30 Open, 40 Obstacle sin aparcar) |
| `no_rule_faults` | ninguna falta (incluye contacto con el muro exterior en el Open) |
| `stop_observed` | parada observada ≥ 30 s simulados |
| `no_contacts` | ningún contacto del robot (sensores de Gazebo), si la ronda los tiene |
| `min_*_clearance_m` | margen muestreado ≥ 1 cm a cada muro / pilar |
| `steering_limit` | dirección medida ≤ 25,5° (25° + tolerancia) |

`margin_class` (no afecta `passed`): **holgado** ≥ 5 cm, **justo** 2–5 cm, **riesgo** < 2 cm.

Antes el Open exigía 5 cm de margen y lo ataba al puntaje; el Obstacle exigía 1 cm. Ahora el
umbral de validez es 1 cm para ambos y el margen se informa aparte.

## Sensores de contacto

- **Pilares** (Obstacle): un sensor por pilar, desde la Fase 0.
- **Muros** (nuevo): un sensor en el link estático `game_field::field` con las 8 colisiones de
  muro, agregado por los runners del Open y del Obstacle. Publica en `/audit/robot_contacts`.
  Prueba de control: la ronda `judge-check2-servo20-v13-shift-ccw` registró 7 roces reales
  de la rueda delantera derecha con el muro exterior.
- Los sensores en el **robot** no funcionan: el sistema de contactos no toma sensores de un
  modelo que aparece después de cargar el mundo (probado también con el plugin en el modelo).
- Como los muros estáticos solo publican al haber contacto, un `contacts.jsonl` vacío cuenta
  como "sin contacto" solo si la copia del mundo de esa ronda tiene el sensor de muros.
- El grabador escribe `contacts-health.json` (mensajes por tópico) como evidencia.

### Formato de `contacts.jsonl`: episodios (9 oct 2026)

Gazebo publica un mensaje de contacto por paso de física (1 kHz) mientras dos cuerpos se
tocan. Con una línea por mensaje, un coche apretado contra un muro escribía ~300 KB por
segundo simulado: una ronda llegó a 249 MB, por encima del límite de GitHub.

Ahora cada línea es un **episodio**: mensajes seguidos de la misma fuente, entre la misma
pieza del coche y el mismo objeto, con huecos de hasta 50 ms simulados
([`contact_log.py`](../src/robotek_evaluation/robotek_evaluation/contact_log.py)). La línea
conserva los campos del primer mensaje (`sim_time` = inicio) y añade `episode`,
`end_sim_time`, `messages` y los máximos de `max_depth`/`points`. Se escribe al empezar el
episodio, cada segundo simulado mientras dura y al terminar; vale la última línea de cada
`episode`. Si el grabador muere, no se pierde ningún primer contacto.

- El juez y los informes leen los dos formatos. Los 34 logs antiguos de más de 1 MB se
  convirtieron con `compact_contacts.py` (en `src/robotek_evaluation/tools/`): 616,5 MB →
  0,5 MB en total.
- **Equivalencia comprobada en las 429 rondas con contactos** (Open y Obstacle): puntos,
  validación, primer contacto por tipo, estado de los pilares y tiempos son idénticos
  antes y después. Única diferencia: `pillar_movements.contact_messages` en 2 rondas
  Obstacle (`audit-check2/3-…-round-v1-ccw`, p. ej. 1016 → 2167). Un episodio que empieza
  antes del final de la ronda cuenta también sus mensajes posteriores, que antes se
  descartaban. El número de mensajes depende del paso de física y no decide ninguna
  clasificación.
- En una ronda nueva, la suma de `messages` coincide con los contactos `kept` de
  `contacts-health.json` (31.690 en `20261009T110757Z-macos-robostack-contactlog-…`).

## Re-juicio de las rondas guardadas

- **Open**: 212 rondas juzgadas (las 24 restantes de `rounds.jsonl` no tienen telemetría o
  eventos suficientes). `points_estimated` pasa a ser el puntaje del juez; el anterior queda en
  `points_estimated_legacy`.
  - 25 → 30 en 30 rondas: el estimador viejo quitaba vuelta y parada a toda ronda que no
    cumplía los 5 cm internos.
  - 27 → 30 en 8 rondas y 30 → 27 en 6: las `extreme-*` viejas solo observaron la parada
    1,04 s (la simulación se cerraba a los 2 s de DONE); sin observación no se cuenta.
  - Diferencias de ±1–8 puntos en rondas incompletas: secciones por huella en vez de por ángulo.
  - 42 rondas viejas con contacto probable con el muro exterior (geometría) y 1 con contacto
    medido por sensor.
- **Obstacle**: 108 rondas completas. La validación nueva coincide con la vieja en 105; 3 pasan
  a no válidas por margen a pilar < 1 cm (`v1c-reg2-cw` 0,3 cm, `v1c-reg3-cw` 0,9 cm,
  `v6-reg1-ccw`). La ronda interrumpida a mano queda marcada `interrupted` y sin puntaje.

Copias previas de los registros: se guardaron fuera del repo antes del re-juicio.

## Reproducción

```bash
cd src/robotek_evaluation/tools
python3 judge_open_runs.py          # Open: todas o rutas concretas
python3 audit_obstacle_runs.py      # Obstacle: re-calcula todas
```

Las rondas nuevas se juzgan solas al terminar (`run_gui_experiment.py`,
`run_obstacle_gui_experiment.py`).

## Límites

- Sigue siendo simulación: no se puede saber si un muro se movió ni cómo resolvería un juez
  los casos ambiguos (por ejemplo, la consecuencia de tocar el muro exterior en el Open).
- Márgenes muestreados a ~10 Hz; los contactos de sensores sí cubren todos los pasos.
- Inicio de ronda: evento `start` del nodo (primer conjunto de sensores), no un botón real.
