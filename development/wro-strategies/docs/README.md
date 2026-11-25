# Documentación — índice

Estado al 9 de octubre de 2026. Toda la documentación y las rondas son de la **simulación
honesta** (solo LiDAR, giroscopio y cámara con ruido) o del coche real. Lo anterior (pose de
Gazebo, sensores ideales) se borró el 9 oct 2026 y queda en el historial de git.

## Empezar aquí

| Documento | Qué es |
|---|---|
| [next-steps.md](next-steps.md) | **Dónde estamos, qué está en curso, cómo retomar y próximos pasos** |
| [paquetes.md](paquetes.md) | **Organización ROS 2**: 7 paquetes (description, gazebo, common, open, obstacle, evaluation, bringup) y sus reglas |
| [robot-real.md](robot-real.md) | **Robot real**: `robot.launch.py`, adaptadores, calibración pendiente |
| [robot-real-pi.md](robot-real-pi.md) | **Pi del coche** (7 oct): acceso SSH, stack del equipo, sensores en RViz desde la Mac, detector de pilares y prueba de servo con la cámara real |
| [ros-robot-controller-oficial.md](ros-robot-controller-oficial.md) | **Placa RRC Lite**: nodo oficial de Hiwonder (MentorPi) leído de GitHub, qué publica y recibe, qué se podría usar y cómo compararlo con el fork del Pi |
| [rrc-lite-motor-2024-vs-ahora.md](rrc-lite-motor-2024-vs-ahora.md) | **Motor de la RRC Lite**: el nodo de 2024 (`ros2_hiwonder`) frente al `rrc_lite_driver` actual (signo, `× 0.75`, tipo de motor) |
| [robot-real-pi/conexiones-sensores.svg](robot-real-pi/conexiones-sensores.svg) | **Cómo conectar los sensores**: USB por controlador, alimentación y GPIO (reporte en SVG) |
| [rrc-lite-pruebas.md](rrc-lite-pruebas.md) | **Pruebas de la placa RRC Lite** en el coche: `rrc_test`, qué comprueba cada función y qué anotar; resultados del 9 oct (zumbador quemado) |
| [rrc-lite/oficial/](rrc-lite/oficial/README.md) | **Documentación oficial de Hiwonder** de la placa: esquemático, protocolo serie, lecciones del firmware (PDF) |
| [robot-real-pi/rename/](robot-real-pi/rename/README.md) | **Renombrado del driver (9 oct 2026):** `ros_robot_controller` → `rrc_lite_driver`, tópicos `/rrc/…`; qué cambió, qué no y cómo deshacerlo |
| [obstacle-deteccion-pilares.md](obstacle-deteccion-pilares.md) | **Detección de pilares**: código del equipo frente al nuestro, qué hace `sensors.launch.py detector:=true` en el coche y qué falta |
| [README: Cómo correr el Open](../README.md#cómo-correr-el-open) | **Cómo correr el Open v5** (la única estrategia del Open): una ronda con GUI, sin ventana, set estándar, laboratorio |

## Reglas y campo

| Documento | Estado |
|---|---|
| [WRO-2026-…-General-Rules.md](WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.md) | Reglas completas 2026 (de PDF) |
| [WRO-2026-…-Open-Challenge-Rules.md](WRO-2026-Future-Engineers-Open-Challenge-Rules.md) | Resumen reglas Open |
| [WRO-2026-…-Gamefield-Specifications.md](WRO-2026-Future-Engineers-Gamefield-Specifications.md) | Campo, asientos, aparcamiento |
| [obstacle-challenge-rules-and-strategy.md](obstacle-challenge-rules-and-strategy.md) | Reglas Obstacle y estrategia inicial |
| [open-challenge-runs/round-scoring.md](open-challenge-runs/round-scoring.md) | Cómo se registran puntos y tiempos por ronda |

## Simulación y validación (vigente)

| Documento | Qué es |
|---|---|
| [simulacion-coche-real.md](simulacion-coche-real.md) | **Perfil `real_car:=true`**: servo, motor y sensores reales; validación Open y límites medidos/inferidos |
| [Mejor Open con coche real](open-challenge-runs/best-realcar-open-round.md) | Mejor ronda GUI, selección por puntos y tiempo, parámetros y evidencia |
| [Historial Open con coche real](open-challenge-runs/realcar-open-history.md) | Cada mejora, qué funcionó y qué falló; enlazado desde la guía de ejecución |
| [guia-inicio-macos-robostack.md](guia-inicio-macos-robostack.md) | **Empezar desde cero en la Mac**: crear el entorno RoboStack, compilar, lanzar Gazebo (solo vista 3D), rondas y problemas frecuentes |
| [roadmap-robot-nuevo.md](roadmap-robot-nuevo.md) | **Qué validar desde cero con el robot nuevo** (medidas del 21 oct 2026): fases, clases, comandos y riesgos |
| [open-reimpl-v5.md](open-reimpl-v5.md) | Plan de reimplementar el Open desde cero con el mínimo de código y estados: ablaciones medidas del v4, diseño (3 estados, 4 campos de observación, ≤12 parámetros), plan de pruebas por capas y criterios de aceptación |
| [open-lab.md](open-lab.md) | Open lab: rondas Open de lazo cerrado en 2 s (campo real, actuadores del coche, juez de Gazebo), qué reproduce de Gazebo y qué no |
| [obstacle-reimpl-plan.md](obstacle-reimpl-plan.md) | Plan y guía de pasos para un agente: reimplementar el Obstacle (v2) con el método del Open v5: medir, laboratorio, diseño mínimo, Gazebo con control de calidad, aparcamiento aparte |
| [simulacion-macos.md](simulacion-macos.md) | **Simular en la Mac** (RoboStack, con o sin ventana): `tools/macos_env.sh`, Metal y Cyclone DDS, `--real-time-factor 2`, atraso intermitente de `/clock` |
| [simulacion-honesta.md](simulacion-honesta.md) | **Simulación honesta**, siempre activa (Open y Obstacle): la estrategia solo ve LiDAR/IMU/cámara con ruido; odometría LiDAR; rumbo por giroscopio |
| [juez-y-validacion.md](juez-y-validacion.md) | Juez de reglas (puntos por reglamento) y validación estándar Open/Obstacle |
| [open-challenge-runs/actuator-model-findings.md](open-challenge-runs/actuator-model-findings.md) | Modelo de actuadores: el "retardo del servo" era el plugin; servo rápido estimado; `open_fastservo_v1–v3` |

## Open Challenge

| Documento | Estado |
|---|---|
| [open-challenge-runs/honest-fsv4-validation.md](open-challenge-runs/honest-fsv4-validation.md) | V4 honesto: square100 8/8; set repetido 35/36; auditoría de chasis y ruedas |
| [mapping-and-racing-investigation.md](mapping-and-racing-investigation.md) | Investigación de mapeo y carrera |

## Obstacle Challenge (sin aparcar)

| Documento | Estado |
|---|---|
| [obstacle-refactor.md](obstacle-refactor.md) | **Vigente**: cómo funciona el Obstacle, `obstacle_sensors_v1`, dónde editar, equivalencia con v8 |
| [obstacle-reimpl-v2.md](obstacle-reimpl-v2.md) | **Obstacle v2**: línea base del coche medido, ablaciones, hallazgos de banco, diseño aprobado y estado de la implementación |
| [obstacle-v2-next-steps.md](obstacle-v2-next-steps.md) | **Qué queda del v2**: semilla 0 y complejidad resueltas, set del laboratorio 3/10, fallos de esquina/color, nodo/launch/runner y archivos de contexto |
| [obstacle-challenge-runs/parking-findings.md](obstacle-challenge-runs/parking-findings.md) | **Estacionamiento**: reglas, mundo `parking`, estrategia, iteraciones (6/6 con 15 pts) |

## Referencias

| Documento | Qué es |
|---|---|
| [../referencias/README.md](../referencias/README.md) | Resultados y estrategias del top 3 mundial 2025 |
| [../referencias/05-analisis-codigo-obstacle-challenge.md](../referencias/05-analisis-codigo-obstacle-challenge.md) | Código Obstacle del top 3 |

## Registros de rondas

- `open-challenge-runs/<fecha>-<nombre>/` y `obstacle-challenge-runs/<fecha>-<nombre>/`: una
  carpeta por intento (también fallidos): `round.json`, `rule_judge.json`, `manifest.json`,
  `params.yaml`, `telemetry.csv`, `contacts.jsonl`, copia del código en `source/`.
  Rondas honestas: además `telemetry.raw.csv` (lo que vio la estrategia) y `audit_pose.csv`.
  Imágenes, scans y logs crudos quedan solo en local (`.gitignore`).
- `open-challenge-runs/rounds.jsonl`, `obstacle-challenge-runs/rounds.jsonl`: ledger de todas.
- Carpeta con `INTERRUPTED.md`: cortada a mano, sin puntaje.
