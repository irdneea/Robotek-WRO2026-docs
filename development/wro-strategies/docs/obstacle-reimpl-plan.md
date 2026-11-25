# Obstacle v2: plan para reimplementarlo desde cero con el mínimo de código (brief para un agente)

> **Para quién es esto:** un agente (Claude Code) que va a hacer con el **Obstacle Challenge** lo mismo que se hizo con el Open
> (ver [open-reimpl-v5.md](open-reimpl-v5.md)): medir qué hace falta, escribir un **laboratorio** rápido, reimplementar con el
> mínimo de estados, parámetros y líneas, y **demostrarlo en Gazebo**. Este documento es el plan y la guía de pasos. Léelo entero
> antes de tocar nada. Lo escribió el agente que hizo el Open, con sus errores incluidos (§3).
>
> **Estado (22 oct 2026): fase 4 en curso, fase 5 sin empezar.** El esqueleto está implementado y el
> laboratorio está en **3/10 válidas**; no se cumple aún el criterio de salida. Estado y pendientes:
> [obstacle-v2-next-steps.md](obstacle-v2-next-steps.md). Resultados y límites:
> [obstacle-reimpl-v2.md](obstacle-reimpl-v2.md). Todo lo que dice «medido» sale del repositorio a
> fecha 22 oct 2026.

## 0. Prompt para pegar al agente

```text
Lee docs/obstacle-reimpl-plan.md y AGENTS.md. Eres el orquestador de la reimplementación del Obstacle Challenge (v2) siguiendo
ese plan, fase por fase. No pases a la fase siguiente sin cumplir los criterios de salida de la actual. Un commit por cambio
verificado (sin trailer de coautoría de IA; push solo si te lo piden, con /usr/bin/git). Código e identificadores en inglés,
prosa y documentos en español. Antes de cada lote de Gazebo comprueba que el equipo está tranquilo. Pregúntame solo las
decisiones de la sección 8. Al terminar cada fase deja un resumen corto con números. Al final documenta el v2 con la guía
learn/04-obstacle-strategy siguiendo la sección 11 (capturas reales con tools/capture/capture_window.sh, esquemas SVG y solution/ ejecutable).
```

## 1. Objetivo y definición de «hecho»

**Objetivo.** Una estrategia de Obstacle (`robotek_obstacle/v2/`) que dé las 3 vueltas de la ronda reglamentaria **sin rozar
pilares ni muros**, con el **menor número de estados, parámetros y líneas** que lo permita, validada con el mismo rigor que el
Open v5, y que **no sea peor** que la estrategia actual en el set estándar. Es **una reimplementación investigada, no una copia
del código actual**: la estrategia actual es una fuente de datos, no una plantilla.

**Hecho** cuando se cumplen *todas*:

1. El v2 pasa el set estándar de Obstacle (semillas 0–4 × CCW/CW = **10 rondas**) en Gazebo, con control de calidad de la máquina,
   con **al menos tantas rondas válidas como la estrategia actual** (hoy 5/10 válidas con 40 puntos; ver §4) y sin peor puntuación.
2. El tiempo medio de ronda no empeora más de la tolerancia que fijes en la fase 0 (por defecto +10 %).
3. Metas de tamaño de la fase 3 cumplidas y medidas **con el mismo método** que la estrategia actual (§9).
4. Hay un laboratorio (`obstacle_lab`) con su pruebas, **con sus límites documentados con honestidad** (§3, §5).
5. Documentación: este plan actualizado con resultados, la guía **`learn/04-obstacle-strategy/`** (con capturas reales, esquemas y solución
   ejecutable, según la [sección 11](#11-cómo-documentarlo-guía-learn04-obstacle-strategy)) y el README con cómo correrlo.
6. El v2 queda **seleccionable** (`strategy:=v2`) pero el valor por defecto **no cambia** hasta que el humano lo decida (§8).

**Fuera de alcance al principio:** el aparcamiento (+22 puntos). Se trata como proyecto aparte (fase 8) y solo si el humano lo pide.

## 2. Reglas del proyecto que no se negocian

Resumen de [AGENTS.md](../AGENTS.md) y de las decisiones del usuario:

- **Simulación honesta:** la estrategia solo usa LiDAR, giroscopio (IMU) y cámara, con ruido. Nada de `/odom_gt`, `/odom`, pose
  de pilares ni `joint_states`. La pose real se graba aparte, solo para auditar.
- **Coche real por defecto:** `real_car:=true` (servo, motor, LiDAR, IMU y cámara medidos). Ganancia `--steer-p-gain 20`.
  Límite de dirección ±25° por regla; el coche real llega a 17,6° (`REAL_STEER_LIMIT`).
- **Candidatos finales con ventana (GUI).** Para iterar se permite `--no-gui --no-rviz --real-time-factor 0` (o `2`).
- **`robotek_obstacle` solo puede depender de `robotek_common`** (nunca de `robotek_evaluation`, del juez, ni del Open).
- **Un refactor no mezcla estrategia**, y no se compara rendimiento sin rondas sin y con GUI. Medidas del coche en
  `robotek_common/vehicle.py`.
- **No editar `src/robotek_evaluation/tools/` ni compilar mientras corre un lote** (los runners corren desde `src`).
- Compilar con `colcon build` (la instalación es una copia: recompila tras cada cambio). Usa **RoboStack**:
  `source tools/macos_env.sh; source install/setup.sh`. Nunca ROS de Homebrew ni el Python del sistema.
- Guardar `round.json` y actualizar `rounds.jsonl` en **cada** ronda, incluso las fallidas; una ronda mal preparada también
  queda registrada. Puntos y tiempos son **estimaciones de simulación**, no puntuación oficial.
- Git: commit por cambio terminado; **sin `Co-Authored-By` de IA**; push solo a petición, con `/usr/bin/git` (el `git` del PATH no
  hace https); reescribir historia exige actualizar los hashes citados en la documentación; ningún archivo de más de 100 MB.
- Código y nombres en **inglés**; prosa, documentos y mensajes al usuario en **español**.

## 3. Lo que aprendimos con el Open (léelo: te ahorra días)

### 3.1 Método que funcionó

1. **Medir antes de diseñar.** Se corrieron 27 rondas de **ablación** en Gazebo (quitar una pieza por vez) y se analizaron las
   rondas ya grabadas. Salió qué piezas eran imprescindibles (cuatro) y cuáles sobraban (varias), y que el 67 % de los giros los
   disparaba una sola señal. Sin eso el v5 habría sido una opinión.
2. **Un laboratorio rápido** (2 s por ronda frente a ~1 min) permitió iterar en el diseño; **Gazebo decide**.
3. **Pruebas por capas:** unitarias con datos armados a mano → laboratorio → Gazebo sin ventana (set estándar) → con ventana → coche real.
4. **El juez de Gazebo reutilizado** sobre las trayectorias del laboratorio: mismos puntos, misma validación.
5. **Una observación inmutable** entre percepción y decisión (`Scene`, 4 campos) y **pocos estados** (3) con las fases como datos.
6. **Subpaquete** `robotek_open/v5/` en vez de un paquete ROS nuevo; el nodo conserva nombre, tópicos y archivos del anterior, así el
   launch, el runner y el juez no cambian; interruptor `strategy:=v5` / `--strategy v5`.

### 3.2 Errores que costaron tiempo (no los repitas)

| Qué pasó | Cómo evitarlo |
|---|---|
| **El laboratorio pasaba lo que Gazebo rechazaba.** Reproducía la línea base, pero no las ablaciones que rompían Gazebo. | Define desde el principio que el laboratorio es **un filtro de un solo sentido**: *fallar ahí es mala señal; pasar ahí no demuestra nada.* Valida su fidelidad con **datos de Gazebo grabados** (§5), no con tu intuición. |
| **Cinemática equivocada.** El laboratorio trataba el coche como un monociclo en `base_link`; Gazebo gira sobre el **eje trasero** (el punto medio se desliza 0,14 rad con la dirección al tope). | Comprueba la cinemática contra la pose real grabada (`audit_pose.csv`) antes de fiarte de nada. |
| **El servo real es más lento que el modelo** (0,10 s de retardo en vez de 0,06). | Identifícalo con **escalones de dirección** en un campo vacío (`tools/open_lab/`). |
| **El equipo estaba cargado** (un juego a 300 % de CPU): el nodo se atrasaba 0,3–2 s respecto al reloj y rechazaba rondas buenas. | Ver §3.3. Nunca saques conclusiones de rondas con atraso. |
| **Nodos huérfanos.** `clean_sim.sh` no mataba `open_strategy_v5`; al interrumpir un lote quedaron nodos publicando órdenes en las rondas siguientes. | Al crear un ejecutable nuevo, añade su patrón a `src/robotek_evaluation/tools/clean_sim.sh` **antes** del primer lote. Tras matar un lote: `clean_sim.sh` y `ps -Ao pid,command \| grep strategy`. |
| **Mi filtro de calidad solo miraba los primeros 13 s** y dejó pasar rondas con atraso al final. | El filtro mira **toda** la ronda (§3.3). |
| **Estimar con una distancia constante** (paralelismo supuesto) falló cuando el coche iba inclinado 0,07 rad. | Prueba tus estimadores con el coche **inclinado y con ruido**, no solo en la pose ideal. |
| **Concluir demasiado pronto de un oráculo sintético** (`golden_open.py` no tenía choques ni actuadores). | El oráculo sirve para detectar que un refactor movió una decisión, no para decidir qué hace falta. |
| **Una ronda marcada «contacto» en el momento equivocado:** el `sim_time` del registro de contactos va ~1 s adelantado respecto al sello del mensaje. | Usa el `stamp` y la trayectoria (`audit_pose.csv`) para ubicar un choque. |

### 3.3 Control de calidad de cada ronda de Gazebo

Una ronda es **utilizable** solo si, en **toda** la ronda: (a) los ticks del control están separados ≤ 0,2 s (`telemetry.csv`, `sim_time`
cada 5 ticks) y (b) el sello de los escaneos no se adelanta al reloj `/clock` más de 0,1 s (`telemetry.csv.scans.jsonl.gz`:
`stamp − sim_time`). Un choque también frena la simulación, así que **un atraso que aparece *después* del primer contacto no
prueba sobrecarga**; uno que aparece *antes*, sí. El Open dejó [`tools/open_suite_quiet.sh`](../tools/open_suite_quiet.sh): espera
carga ≤ 8 (`sysctl -n vm.loadavg`) y repite hasta 3 veces una ronda que se atrasó. **Haz un equivalente para el Obstacle**
(`tools/obstacle_suite_quiet.sh`). Si el humano tiene apps pesadas abiertas, **pídele que las cierre** (una app «en pausa» sigue
gastando CPU); no las cierres tú.

### 3.4 Trampas del entorno

- El shell tiene `noclobber`: `>` no sobrescribe archivos; usa `>|`, o escribe con Python.
- zsh no separa palabras en variables sin comillas: usa **arrays** para listas de argumentos.
- `python3 - <<EOF` con `multiprocessing.Pool` falla (no hay `__main__`): guarda el script en un archivo.
- Entorno RoboStack: `source tools/macos_env.sh >/dev/null 2>&1` y **después** `colcon build`; un `colcon build` hecho con variables de
  Homebrew encadena `/opt/homebrew` en `install/setup.sh` (`grep -c homebrew install/setup.sh` debe dar 0).
- `pytest`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=$(ls -d src/*/ | tr '\n' ':') python3 -m pytest ... --ignore=src/rrc_lite_driver`.
- No lances barridos con más de 4 procesos y pon `tmax` a las rondas de laboratorio; un barrido largo dejó el Mac en 100 % de CPU.
- Resultados de un lote con `tail` no salen hasta el final: redirige a un archivo y lee ese archivo.

## 4. Estado actual del Obstacle (medido)

**Ronda reglamentaria:** misma pista 3×3 m del Open, corredor de 1 m, **pilares rojo/verde de 50×50×100 mm**
(verde: pasar dejándolo a la derecha del coche; rojo: a la izquierda; §9.19), 3 vueltas, 3 minutos. Máximo 62 puntos: **40 por las
vueltas** y **22 por aparcar** ([reglas](obstacle-challenge-rules-and-strategy.md)). La prueba estándar del proyecto: **semillas
0–4 en ambos sentidos** (`--seed N --direction ccw|cw`).

**Código** (`src/robotek_obstacle/robotek_obstacle/`, mismo contador de líneas y complejidad que el Open, §9):

| Módulo | Líneas | Complejidad | Función más compleja | Qué hace |
|---|---|---|---|---|
| `obstacle_mission.py`, `_driver.py`, `_beam_planner.py`, `_localizer.py`, `_seat_map.py`, `_perception.py`, `_field.py` | 723 | 227 | 15 | misión (`CALIBRATE`→`DETECT_DIRECTION`→driver `PLAN…DONE`), localizador contra muros, mapa de 24 asientos con voto de color, planificador de haz sobre secuencias de volante, seguimiento por persecución pura, percepción (clústeres del LiDAR + manchas de color) |
| `obstacle_parking.py` | 303 | 124 | 30 | aparcamiento (aparte) |
| `obstacle_strategy_node.py`, `obstacle_detector_node.py` | 347 | 88 | 19 | nodos ROS |

`ObstacleConfig`: **16 parámetros** de ROS y **32 valores fijos**. El perfil `obstacle_sensors_v1.yaml` solo fija `direction: auto`.
Hay **una sola prueba** en el paquete (`test_obstacle_perception.py`).

**Resultados conocidos** (README, 21 oct 2026): semillas 0–4 × CCW/CW → **10/10 con 40 puntos**, tiempo medio **72 s**, sin
contactos, pero solo **5/10 válidas**: pasadas a < 1 cm de muros/pilares (la validación exige ≥ 1 cm; «cómodo» ≥ 5 cm).
3 rondas con GUI válidas. Falta margen y el aparcamiento. Las rondas conocidas problemáticas: trampas del planificador en
`reg1-ccw` (ver [obstacle-refactor.md](obstacle-refactor.md) y `docs/next-steps.md`).

**Herramientas existentes:** runner `run_obstacle_gui_experiment.sh` (`--name --seed --direction --profile --param --no-gui --no-rviz
--steer-p-gain --real-time-factor --launch-arg --wall-timeout`), lote `run_obstacle_batch.sh <prefijo> <perfil> "<semillas>"
"<sentidos>"`, preparación `obstacle_experiment_setup.py`, informes `obstacle_full_round_report.py` (puntos por vueltas y pilares)
y `obstacle_parking_report.py`, auditoría `audit_obstacle_runs.py`, equivalencia `check_obstacle_refactor_equivalence.py`,
`obstacle_audit_recorder`/`audit_pose_recorder` (verdad de pose y contactos, solo para auditar).

**Lo que NO existe y hay que construir:** (1) un **juez de Obstacle** como el `judge_open` del Open (hoy el Obstacle se puntúa con
`obstacle_full_round_report.py`; **verifica** si basta para reutilizarlo en el laboratorio); (2) el **laboratorio**; (3) las
**ablaciones**; (4) el **control de calidad** de lotes; (5) el comparador de sets (`compare_open_suites.py` es del Open).

**Dato clave para investigar:** cada ronda grabada guarda **`trace.jsonl.gz`** con *todas* las entradas (IMU, escaneos,
observaciones de cámara) y las **órdenes de cada ciclo**. Eso permite **reproducir** una ronda y comparar decisiones: úsalo.

## 5. Plan por fases

Cada fase tiene **qué hacer**, **cómo** y **criterio de salida**. Haz un commit por entregable.

### Fase 0 · Línea base y herramientas de medida

**Qué.** Fijar el patrón contra el que vas a comparar y cómo medirlo.

1. **Línea base de Gazebo.** Corre el set estándar (semillas 0–4 × CCW/CW) con la estrategia actual **dos veces** (etiquetas `obs-base-a`,
   `obs-base-b`) con la máquina tranquila (§3.3). La diferencia entre las dos es la **dispersión de referencia** (con ruido, dos
   corridas idénticas no dan lo mismo; en el Open llegó a 1,0 s).
2. **Escribe `tools/compare_obstacle_suites.py`** (copia la lógica de `tools/compare_open_suites.py`: por ronda, el candidato debe quedar
   dentro de la dispersión de referencia más una holgura; añade puntos, validez y margen mínimo).
3. **Escribe `tools/obstacle_suite_quiet.sh`** (copia `tools/open_suite_quiet.sh`: espera carga ≤ 8, comprueba **toda** la ronda,
   repite hasta 3 veces). Añade su ejecutable a `clean_sim.sh` si creas uno nuevo.
4. **Contador de tamaño** (§9) y **medidas de la estrategia actual** (líneas, complejidad total y máxima, parámetros, estados).
5. **Decide el criterio de «válida»** leyendo `standard_validation` (`rule_judge.py`) y `obstacle_full_round_report.py`. Anota qué
   cuenta como falta (tocar pilar fuera del círculo, lado equivocado, tocar muro).

**Salida.** Documento de línea base con tablas (rondas, puntos, tiempo, margen, válidas), la dispersión de referencia y las medidas de tamaño.

### Fase 1 · Investigación: qué hace falta de verdad

**Qué.** Antes de diseñar nada, **medir**. Es la fase más importante.

1. **Mapa de la estrategia actual.** Dibuja (en un SVG o en una tabla) qué decide cada módulo, qué datos recibe y de qué depende. Anota
   los parámetros y valores fijos y cuáles **toca algún perfil** (`profile.yaml` de las rondas ya grabadas). Busca **código muerto**:
   no hay `vulture` instalado (el entorno `robotek-tools` no existe); usa la comprobación por AST del Open (definiciones sin lectores, campos
   de configuración que nadie lee). No instales paquetes en el Python del sistema.
2. **Análisis de rondas grabadas** (`docs/obstacle-challenge-runs/`): ¿cuánto tiempo pasa en cada fase (`PLAN`, retroceso, `FINISH`)? ¿Cuántas veces
   retrocede? ¿Qué rondas fallaron y por qué (choque con muro, con pilar, lado equivocado, trampa del planificador)? ¿Qué distancia
   mínima tiene cada ronda **y cuándo**? Usa `trace.jsonl.gz` y `audit_pose.csv`.
3. **Ablaciones en Gazebo** (una pieza por vez, tres o cuatro rondas por pieza en semillas distintas, sin ventana a ×2, máquina
   tranquila). Candidatas, a confirmar leyendo el código: sin localizador (`plan_loc_gain=0`); sin voto de color del mapa de asientos
   (¿cuánto aporta la cámara frente al LiDAR?); sin penalización de lado (`plan_side_cost`); sin recompensa de vista (`plan_view_gain`);
   horizonte y haz más cortos (`plan_steps`, `plan_beam`); sin retroceso (`recover`); sin compensación de latencia; sin término de
   rumbo final; velocidades (`plan_speed`, `plan_lat_accel`). Se hacen con `--param nombre=valor` (los valores fijos requieren un
   parche temporal: hazlo en una rama, no en `main`). Guarda el script en `tools/obstacle_param_ablation.sh` (modelo:
   `tools/open_param_ablation.sh`).
4. **Cuidado al interpretar fallos:** comprueba el atraso del nodo (§3.3) y **que el primer contacto ocurra antes que los atascos del lazo**.
   Un fallo por carga no es una ablación. Repite lo dudoso.
5. **Pregunta de fondo (documéntala con datos):** ¿para qué sirve cada una de las tres grandes piezas, *localizador*, *mapa de asientos* y
   *planificador de haz*, y existe una alternativa **mucho más simple** que dé los mismos márgenes? Ejemplos para evaluar, no para
   asumir: (a) conducir por el corredor con un **desplazamiento lateral por pilar** decidido al ver el pilar (color → lado), como lo
   resuelven otros equipos; (b) reducir el planificador a pocas trayectorias candidatas (por ejemplo, desplazamientos laterales fijos)
   en vez de un haz de secuencias de volante; (c) localizarse solo con los muros (ya se hace) y dejar de mantener los 24 asientos si
   basta con «el próximo pilar». Mide, no supongas.
6. **Hallazgos aparte** (como los del Open: el contorno viejo del coche en el juez, el `wheelbase=0.13` del modelo de actuadores…): si
   encuentras defectos del banco de pruebas, **documéntalos y no los arregles dentro de este trabajo** salvo que bloqueen.

**Salida.** `docs/obstacle-reimpl-v2.md` (hallazgos, tablas de ablación, mapa de la estrategia, decisión razonada de qué se conserva) y una
lista de **hipótesis H-O1…** con su experimento (formato del [plan del Open](open-reimpl-v5.md#6-hipótesis-a-probar-cada-una-con-su-experimento)).

### Fase 2 · Laboratorio del Obstacle (`obstacle_lab`)

**Qué.** Un simulador de lazo cerrado de pocos segundos por ronda, **como filtro**, copiando la estructura de
[`open_lab.py`](../src/robotek_evaluation/robotek_evaluation/open_lab.py) y [open-lab.md](open-lab.md). Lo que ya está resuelto y se reutiliza:
`Actuators` (copia de `SimActuatorModel` con `real_car_v1.yaml` y el servo medido: retardo 0,10 s, 1,2 rad/s, filtro 0,06 s), cinemática
de **eje trasero**, el modelo del LD19 (10 Hz, 306 rayos a ±110°, ruido de 8 mm, 4,3 % de pérdidas, cada escaneo entregado **3 veces**),
el giroscopio (50 Hz, sesgo 0,006 rad/s, ruido 0,0019), `LidarOdometry` real, y un adaptador de estrategia con
`on_scan/on_imu/on_camera/control`.

**Lo nuevo del Obstacle (lo que debes construir):**

1. **Mundo con pilares.** Cajas de 50×50×100 mm en los asientos de la distribución reglamentaria. Reutiliza el generador de
   distribuciones de `obstacle_experiment_setup.py` (la semilla fija la distribución) y los muros del SDF del campo.
2. **Rayos contra pilares** (rectángulos) además de los muros; el LiDAR ve los pilares como clústeres cortos.
3. **Modelo de cámara.** No simules imágenes: genera **observaciones** (rumbo y color de cada pilar visible dentro del campo de visión de
   la cámara real, `REAL_CAMERA_HFOV`, con alcance, ruido de rumbo y probabilidad de acierto de color **medidos contra rondas
   grabadas**). Define el formato mirando lo que consume `obstacle_perception.py` y lo que graba `trace.jsonl.gz`.
4. **Juez del Obstacle.** Reutiliza `obstacle_full_round_report.py` (puntos y pilares) y `standard_validation`. Si el informe necesita
   archivos de una ronda de Gazebo, escribe filas equivalentes como hizo `open_lab._row`. Añade: lado correcto por pilar, pilar
   movido fuera del círculo, contactos con muros y pilares, margen mínimo.
5. **Contactos:** una colisión termina la ronda (como en el Open); la geometría del coche es el contorno medido de `vehicle.py`.

**Cómo validar el laboratorio (obligatorio, con datos grabados de Gazebo):**

- **LiDAR:** reproduce los escaneos de una ronda grabada (`telemetry` o `trace.jsonl.gz`) con la pose real (`audit_pose.csv`) y compara rango a rango:
  debe coincidir al nivel del ruido (en el Open: ±1,4 cm y 4,3 % de rayos vacíos). **Incluye los pilares.**
- **Cámara:** compara las observaciones que el laboratorio daría en las poses de una ronda real con las que grabó el nodo (alcance, rumbo,
  color). Mide la tasa de confusión de color y el retraso.
- **Plantas:** con los escalones de dirección de `tools/open_lab/` (rueda: retardo 0,10 s, 1,2 rad/s, filtro 0,06 s; cuerpo: sin retardo
  respecto al ángulo medido) ya identificados para el Open. Verifica que valen para el Obstacle (mismo coche, mismo modelo de actuadores).
- **Línea base cerrada:** la estrategia **actual** en el laboratorio, 10 rondas, debe parecerse a Gazebo: mismas rondas válidas/no
  válidas **y** márgenes mínimos parecidos (±2 cm), tiempos dentro de ~5 %. **Si no, no lo uses para decidir nada**; documenta la diferencia.
- **Ablaciones:** repite en el laboratorio las de la fase 1 y compáralas con Gazebo. **Reporta lo que no reproduce** (en el Open falló y
  eso quedó escrito).

**Reglas del laboratorio:** filtro de un solo sentido (§3.2); **tmax** por ronda (180 s de reloj de pista; el Obstacle dura más que el
Open) y ≤ 4 procesos en paralelo; pruebas en `src/robotek_evaluation/test/test_obstacle_lab.py`.

**Salida.** `open_lab`-equivalente funcionando, con tabla de fidelidad (qué coincide con Gazebo y qué no) y pruebas.

### Fase 3 · Diseño del v2

**Qué.** Con los datos de las fases 1 y 2, define el diseño **más pequeño** que cumpla. Entregable: sección «Diseño» en
`docs/obstacle-reimpl-v2.md`.

- **Principios (del Open):** una observación inmutable de pocos campos; pocos estados y las fases como datos; constantes del coche en
  `vehicle.py`; parámetros solo para lo que se ajusta en pista (meta: **≤ 12**); el nodo ROS, la visión y la telemetría se
  **conservan**; el v2 **solo importa `robotek_common`**.
- **Metas de tamaño** (confírmalas con los datos de la fase 0; propuesta inicial, no un mandato): estados ≤ 4 (más un motivo de parada),
  campos de la observación ≤ 8, parámetros ≤ 12, líneas de decisión+percepción ≤ la mitad de las 723 actuales (**sin parking**),
  función más compleja ≤ 10.
- **Qué se quita y por qué** (con la evidencia de la ablación) y **qué se conserva y por qué**.
- **Contrato de datos:** define qué ve la decisión por tick (por ejemplo, distancia a muros, lista corta de pilares con lado y color,
  distancia recorrida) y qué devuelve (velocidad y dirección).
- **Lo que el v2 aún no hace** (aparcar, recuperar atascos, etc.): decláralo como límite, no como mejora.
- **Hipótesis** con su experimento y su plan B si fallan (como la tabla §6 del Open).

**Salida.** Diseño revisado por el humano **antes de implementar** (§8, decisión 1).

### Fase 4 · Implementación y pruebas de capa 1

**Qué.** `src/robotek_obstacle/robotek_obstacle/v2/` (subpaquete, **sin** `package.xml` nuevo), con la estructura del Open v5:
`scene.py` (o equivalente) + `mission.py` + `settings.py` (parámetros de ROS y su validador) + `recording.py`. Pruebas unitarias en
`src/robotek_obstacle/test/` **sin simulador** con datos armados a mano: cada decisión (lado de cada color, margen a un pilar,
retroceso, parada final) y cada estimador con **inclinación y ruido** (§3.2). Adaptador `V2Strategy` en el laboratorio y filtro
de laboratorio ronda a ronda, **antes** del nodo.

**Salida.** Pruebas pasando y 10/10 válidas **en el laboratorio** con la dispersión que el filtro permita; medidas de tamaño.

### Fase 5 · Nodo ROS, launch y runner

**Qué.** `v2/node.py` (`obstacle_strategy_v2`, **nodo con el mismo nombre** `obstacle_strategy`, mismos tópicos, reloj y archivos que el actual),
perfil `config/obstacle_v2.yaml`, entrada en `setup.py`, interruptor `strategy:=v2` en el launch del Obstacle y `--strategy v2` en el
runner, `clean_sim.sh` con el patrón del ejecutable nuevo, y el manifiesto de la ronda con la estrategia y su configuración. Mira cómo
lo hizo el Open: `src/robotek_open/robotek_open/v5/node.py`, `src/robotek_bringup/launch/open_challenge.launch.py`,
`src/robotek_evaluation/robotek_evaluation/open_experiment_setup.py` y `run_gui_experiment.py`. La telemetría debe usar **las mismas
columnas** que lee `summarize` (si una columna falta como `nan`, `int()` falla: rellena valores por defecto) y los **nombres de estado**
que lee el juez y los informes. **No cambies el valor por defecto.**

**Salida.** Una ronda de humo en Gazebo con puntos y `validation` correctos.

### Fase 6 · Set estándar en Gazebo y comparación

**Qué.** `tools/obstacle_suite_quiet.sh v2-a` (10 rondas con control de calidad) y
`python3 tools/compare_obstacle_suites.py obs-base-a obs-base-b vs v2-a`. Repite el set al menos **dos veces** (el ruido lo exige). Las
rondas contaminadas se conservan como intentos y se anotan; cada campo debe tener rondas **limpias**.

**Si el v2 falla en Gazebo y no en el laboratorio:** es lo esperado de un filtro indulgente. Depura con la **verdad de Gazebo**: las
rondas grabadas (`trace.jsonl.gz`, `audit_pose.csv`) y la comparación de trayectorias con el laboratorio. Corrige la causa
(en el Open fue una estimación que suponía paralelismo).

**Salida.** Tabla v2 contra línea base: válidas, puntos, tiempo, margen mínimo por ronda y la dispersión de referencia.

### Fase 7 · Ventana, documentación y entrega

1. Rondas **con ventana** a velocidad normal (por ejemplo `reg0` CCW y CW), también con control de calidad.
2. `docs/obstacle-reimpl-v2.md` con resultados; actualizar **este** plan con lo hecho; **`learn/04-obstacle-strategy/`**: guía por pasos como
   `learn/03-open-strategy`, con capturas reales, SVG y un `solution/` ejecutable (procedimiento completo en la [sección 11](#11-cómo-documentarlo-guía-learn04-obstacle-strategy));
   README con «Cómo correr el Obstacle» y el estado.
3. Nota de memoria si aprendes algo no obvio del equipo (ver `~/.claude/projects/.../memory/`).
4. Informe final corto (§7). Push solo si el humano lo pide.

### Fase 8 · Aparcamiento (opcional, aparte)

Solo si el humano lo decide (§8, decisión 3). El aparcamiento (`obstacle_parking.py`: 303 líneas, complejidad máxima 30) es la pieza
más compleja del paquete. Aplica **el mismo método** (medir → laboratorio con el parking y los elementos magenta → diseño mínimo → Gazebo
con `--layout parking` y el informe `obstacle_parking_report.py`). No lo mezcles con las vueltas: otro plan, otra rama de commits.

## 6. Hipótesis iniciales para evaluar (el agente las confirma o las descarta)

| # | Hipótesis | Experimento | Si falla |
|---|---|---|---|
| H-O1 | El voto de color de la cámara es la única señal necesaria para el **lado**; el LiDAR basta para el **dónde** | ablación sin color (todos del mismo lado) y con color ruidoso en el laboratorio | conservar el voto de varios cuadros |
| H-O2 | No hace falta mantener los 24 asientos: basta el **próximo pilar** en el campo de visión | laboratorio y Gazebo con una lista corta | volver al mapa |
| H-O3 | Un conjunto pequeño de trayectorias candidatas (desplazamientos laterales) iguala al haz de secuencias de volante | mismo set, mismos márgenes | planificador reducido, no eliminado |
| H-O4 | El localizador contra muros se puede reemplazar por la **distancia a los muros laterales** y el giroscopio | ablación `plan_loc_gain=0`; márgenes | conservarlo |
| H-O5 | `plan_latency`, `plan_feedback` y los costes secundarios del planificador no hacen falta | ablaciones | dejar solo los que pesen |
| H-O6 | El estado final (`FINISH`) es una fase y no un estado | como en el Open | — |
| H-O7 | La **dirección** del Obstacle se decide solo con muros (la cámara de respaldo no hace falta) | rondas donde el LiDAR gana en el primer escaneo | conservar la cámara |

Son puntos de partida: la fase 1 puede refutar cualquiera.

## 7. Informe de cada fase (formato)

Al terminar cada fase, un mensaje corto con: **qué se hizo** (1–3 líneas), **números** (tabla), **límites o dudas** y **qué sigue**. Sin
adornos. Si algo no se pudo medir, dilo; si una conclusión depende de un laboratorio indulgente, dilo.

## 8. Decisiones que son del humano (pregunta, no asumas)

1. **Aprobar el diseño** de la fase 3 antes de implementar.
2. **Cambiar el valor por defecto** del Obstacle al v2 (solo tras Gazebo limpio y ventana; el coche real sigue con la estrategia que ya
   conoce hasta que se pruebe allí).
3. **El aparcamiento** (+22 puntos): ¿en alcance? ¿cuándo?
4. **Tolerancia de tiempo** (+10 % por defecto) y **qué valida** una ronda (por ejemplo, exigir margen «justo» o solo ≥ 1 cm).
5. **Push** a `main`.

## 9. Anexo: cómo medir el tamaño (mismo método antes y después)

Sin comentarios ni docstrings; complejidad = `if`, `for`, `while`, comprensiones, `except`, `IfExp` y cada `and`/`or`; la «más compleja»
es la función con mayor valor. Guarda este script como `tools/code_metrics.py` y úsalo en la línea base y al final:

```python
import ast, sys

def complexity(fn):
    n = 1
    for x in ast.walk(fn):
        if isinstance(x, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.comprehension, ast.IfExp)):
            n += 1
        elif isinstance(x, ast.BoolOp):
            n += len(x.values) - 1
    return n

lines = total = worst = 0
for path in sys.argv[1:]:
    src = open(path).read()
    tree = ast.parse(src)
    docs = set()
    for x in ast.walk(tree):
        if isinstance(x, (ast.Module, ast.ClassDef, ast.FunctionDef)) and x.body and isinstance(x.body[0], ast.Expr) \
                and isinstance(getattr(x.body[0], 'value', None), ast.Constant) and isinstance(x.body[0].value.value, str):
            docs.update(range(x.body[0].lineno, x.body[0].end_lineno + 1))
    lines += sum(1 for i, l in enumerate(src.split('\n'), 1)
                 if l.strip() and not l.strip().startswith('#') and i not in docs)
    values = [complexity(x) for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]
    total += sum(values)
    worst = max(worst, max(values or [0]))
print(lines, total, worst)     # lines of code, total complexity, most complex function
```

## 10. Anexo: mapa de archivos y comandos

| Qué | Dónde |
|---|---|
| Estrategia actual | `src/robotek_obstacle/robotek_obstacle/` (config, field, localizer, seat_map, beam_planner, driver, mission, perception, parking, nodos) |
| Modelo a copiar (Open v5) | `src/robotek_open/robotek_open/v5/` (`scene.py`, `mission.py`, `settings.py`, `recording.py`, `node.py`) |
| Laboratorio a copiar | `src/robotek_evaluation/robotek_evaluation/open_lab.py` + `test_open_lab.py` + [open-lab.md](open-lab.md) |
| Identificación del servo | `tools/open_lab/` (`steer_id.launch.py`, `steer_id_drive.py`, `steer_id_fit.py`) |
| Ablaciones del Open | `tools/open_param_ablation.sh`, `tools/open_ablation_synthetic.py` (borrados con el v4 el 26 oct 2026; en la historia de git) |
| Lote con control de calidad | `tools/open_suite_quiet.sh`; limpieza: `src/robotek_evaluation/tools/clean_sim.sh` |
| Capturas de ventanas (Gazebo, RViz) | `tools/capture/capture_window.sh` (`--list` para ver ventanas) y `list_windows.swift` |
| Guía a imitar | `learn/03-open-strategy/` (README, `img/`, `solution/`) y `learn/02-sensors-rviz/` |
| Runner del Obstacle | `src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh`, `run_obstacle_batch.sh` |
| Preparación y distribuciones | `src/robotek_evaluation/robotek_evaluation/obstacle_experiment_setup.py`, `obstacle_field.py` (estrategia) |
| Informes y juez | `obstacle_full_round_report.py`, `obstacle_parking_report.py`, `rule_judge.py` (`standard_validation`) |
| Reglas | [obstacle-challenge-rules-and-strategy.md](obstacle-challenge-rules-and-strategy.md), `docs/WRO-2026-Future-Engineers-*` |
| Qué tiene el Obstacle hoy | [obstacle-refactor.md](obstacle-refactor.md), [obstacle-deteccion-pilares.md](obstacle-deteccion-pilares.md), [next-steps.md](next-steps.md) |

```bash
# Entorno y compilación (siempre así; nunca con variables de Homebrew)
source tools/macos_env.sh >/dev/null 2>&1; colcon build --packages-select robotek_obstacle robotek_evaluation robotek_bringup
source install/setup.sh >/dev/null 2>&1; grep -c homebrew install/setup.sh        # debe dar 0

# Una ronda reglamentaria (estrategia actual), sin ventana
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh --name obs-prueba --seed 0 --direction ccw \
  --steer-p-gain 20 --launch-arg real_car:=true --no-gui --no-rviz --real-time-factor 2 --wall-timeout 320

# Las 10 rondas del set estándar (sin control de calidad: úsalo solo para humo)
bash src/robotek_evaluation/tools/run_obstacle_batch.sh obs-base-a src/robotek_obstacle/config/obstacle_sensors_v1.yaml \
  "0 1 2 3 4" "ccw cw" --steer-p-gain 20 --launch-arg real_car:=true --no-gui --no-rviz --real-time-factor 2

# Pruebas
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=$(ls -d src/*/ | tr '\n' ':') python3 -m pytest src/robotek_obstacle src/robotek_evaluation -q --ignore=src/rrc_lite_driver
```

## 11. Cómo documentarlo: guía `learn/04-obstacle-strategy/`

La guía es parte del entregable (no un extra): obliga a entender el v2 de punta a punta y es lo que lee el equipo. **Se escribe cuando el
diseño ya está estable (después de la fase 6) y sobre el código real, nunca sobre el plan.** El modelo es
[`learn/03-open-strategy/`](../learn/03-open-strategy/README.md); mírala entera antes de empezar.

### 11.1 Formato (copia el de la guía 3)

- **Cabecera:** «Qué vas a conseguir» (una frase), **Nivel** (secundaria con algo de Python), **Tiempo**, **Antes** (guías 2 y 3 y la
  [guía de inicio](guia-inicio-macos-robostack.md)), una nota con la fecha y el estado real de la estrategia (**con sus límites**: lo
  que aún no hace, lo no probado en el coche), un esquema general y el **índice** de pasos.
- **Pasos numerados**, cada uno corto: una idea, un esquema o una captura, y algo que el lector **ejecuta o mira**.
- **Un `solution/`** con una versión mínima **ejecutable sin ROS** y sus pruebas, más la salida real pegada en la guía.
- **Cierre:** problemas frecuentes (tabla), retos (4–5, con pistas), glosario y una nota final con la ronda de referencia (nombre,
  puntos, tiempos) y el número real de pruebas que pasan.
- **Idioma:** prosa en español, código e identificadores en inglés. Sin jerga sin definir; los términos nuevos van al glosario.

### 11.2 Esquema de pasos propuesto (ajústalo al diseño real)

1. Qué es el Obstacle y cómo se puntúa (pilares, lado correcto, 40 + 22 puntos, círculo del asiento, faltas).
2. Lo que recibe el coche (LiDAR, giroscopio y **cámara de color**; sin encoder ni pose).
3. Lanzar una ronda reglamentaria con ventana y RViz (comando del runner, `--seed`, `--direction`).
4. Ver el campo con pilares en Gazebo.
5. Ver lo que ve el coche en RViz (escaneo, pilares detectados, clústeres, color).
6. La percepción del v2 (qué números salen del LiDAR y de la cámara; la observación inmutable).
7. Decidir el **lado** de cada pilar (color → lado) y por dónde pasar.
8. Planificar y seguir la trayectoria (el corazón del v2, **tal como quedó tras la fase 3**).
9. La máquina de estados y la parada.
10. Una ronda de punta a punta y cómo leer `round.json` y el informe de pilares.
11. Probar sin el coche (pruebas del v2 y el laboratorio, con su límite de «filtro»).
12. Con el coche (qué falta probar y qué cuidar).
13. Del v1 al v2 (tabla de tamaño y resultado en Gazebo, y qué se quitó por qué; el aparcamiento si quedó fuera).

### 11.3 Procedimiento, en orden

1. **Elige la ronda de referencia:** una ronda **limpia** (control de calidad, §3.3) con ventana y `--real-time-factor 1`, p. ej. semilla 0
   CCW. Anota de su `round.json`: puntos, tiempo desde Start (reloj de simulación y de pared), vueltas, margen mínimo. **Todos los números
   de la guía salen de ahí o del set estándar documentado**; no inventes ninguno.
2. **Capturas reales de Gazebo y RViz.** Esas dos aplicaciones **no se pueden controlar con computer use**: se capturan **por ventana**
   con `tools/capture/capture_window.sh` (usa `screencapture -l <id>`; la primera vez macOS pide permiso de *Grabación de pantalla* a la
   app que ejecuta el comando). Pasos:
   - Lanza la ronda de referencia **en segundo plano** con ventana y `--rviz`; mira `tools/capture/capture_window.sh --list gz` y `--list rviz`
     para ver los ids; si hay varias ventanas de Gazebo, prueba hasta dar con la vista 3D.
   - Captura **a intervalos** mientras la ronda corre (p. ej. un bucle `for t in 1 4 8 12 …; do sleep …; capture …; done`) y elige después las
     mejores. Momentos que valen: salida (pilares visibles), una **pasada junto a un pilar** (rojo y verde) y el final. En RViz: el escaneo
     con los pilares detectados y los clústeres.
   - **Mira cada imagen con la herramienta `Read`** antes de usarla (ventana correcta, nada confidencial, texto legible). Reduce a ≤ 1,4 mil px
     de ancho con `sips -Z 1400 archivo.png` y que cada una pese menos de 1 MB. Nómbralas `img/NN-descripcion.png` y pon un pie que diga **qué
     ronda** y **qué momento** son.
3. **Esquemas SVG** (3 a 5): pipeline de sensores a `/cmd_vel`, máquina de estados, cómo se decide el lado de un pilar, cómo se elige/sigue la
   trayectoria. Estilo de `learn/03-open-strategy/img/` (verde: ruta normal, azul: proceso, naranja: recuperación, rojo: parada).
   Genéralos con un script de Python (cajas, flechas con `marker`, etiquetas) y **comprueba el render**: `qlmanage -t -s 1000 -o /tmp
   img/NN.svg` y abre el PNG con `Read` (la miniatura sale recortada a un cuadrado; fíjate en que ningún texto se salga de su caja ni se
   superponga).
4. **`solution/mini_obstacle.py` + `test_mini_obstacle.py`:** la idea central del v2 en unas 80–100 líneas, sin ROS, con el **mismo código**
   (mismas funciones y constantes) que el v2 real simplificado al mínimo. Debe imprimir una salida que la guía pegue literalmente, y tener 5–8
   pruebas que fallen si quitas una condición (como `should_turn` en la guía 3). Nota en el código si el coche simulado ignora algo que el real
   no (retraso del servo, ruido).
5. **Escribe la guía** con ese material. Cada comando que aparezca se **ejecuta de verdad** antes de dejarlo; pega la salida real.
6. **Verificación antes del commit** (todo con comandos, no a ojo):
   - enlaces relativos y de imágenes existen (script que recorre `](…)` y comprueba que el archivo existe);
   - los números de la guía coinciden con `round.json`, el set estándar y `docs/obstacle-reimpl-v2.md`;
   - `python3 mini_obstacle.py` y las pruebas de `solution/` pasan y su salida coincide con la de la guía;
   - sin referencias a lo que ya no existe; pronombres neutros si hablas de personas (sin género).
7. **Enlaza la guía** desde `docs/README.md`, el README principal (sección del Obstacle) y el roadmap, y commitea (un commit para la guía).

### 11.4 Lo que debe quedar claro en la guía (honestidad)

Qué hace el v2 y **qué no** (por ejemplo, sin aparcar o sin recuperación de atascos); que el **laboratorio** es un filtro; que lo medido
en Gazebo con la máquina tranquila es lo que cuenta; qué sigue **sin probar en el coche real**; y que las capturas son de **una** ronda
concreta (nómbrala). Si algo cambió respecto al plan (§6), explícalo en el paso «Del v1 al v2».

*Plan escrito el 21 oct 2026 por el agente que hizo el Open v5 ([evidencia](open-reimpl-v5.md), [laboratorio](open-lab.md),
[guía](../learn/03-open-strategy/README.md)). Los comandos del Open v5 están verificados; los del Obstacle son los del runner actual y hay
que comprobarlos en la fase 0 antes de fiarse.*
