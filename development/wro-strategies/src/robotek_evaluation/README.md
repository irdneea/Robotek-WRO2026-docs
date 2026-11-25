# robotek_evaluation

Todo lo que **solo existe en simulación** y no debe usar ninguna estrategia:

| Módulo / nodo | Qué hace |
|---|---|
| `audit_pose_recorder` | Graba pose real (`/odom_gt`), odometría ideal y ángulo de ruedas en `audit_pose.csv` |
| `obstacle_audit_recorder` | Contactos con muros/pilares y pose real de los pilares (`contacts.jsonl`, `pillars-gt.jsonl`). Los contactos se guardan por episodio (`contact_log.py`); `tools/compact_contacts.py` convierte los logs antiguos |
| `sim_actuator_model` | Servo y motor estimados entre la estrategia y el plugin de Gazebo |
| `rule_judge.py`, `open_round_report.py`, `obstacle_full_round_report.py` | Puntos por reglas, validación estándar, reportes por ronda |
| `open_experiment_*.py`, `obstacle_experiment_setup.py`, `open_field_geometry.py` | Preparación de mundos/perfiles, supervisión y métricas de los runners |

Depende de `robotek_open` y `robotek_obstacle` (para validar perfiles y copiar su
código en cada ronda); ninguna estrategia depende de este paquete.

Runners (desde la raíz del repo, tras `colcon build` y `source install/setup.zsh`):

```bash
# Open
bash src/robotek_evaluation/tools/run_gui_experiment.sh <nombre> \
  --params-file src/robotek_open/config/open_sensors_v1.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction ccw --controller-direction auto --spawn-y -1.15 \
  --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 --launch-arg actuator_model:=true
# Obstacle (perfil por defecto obstacle_sensors_v1)
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh --name <nombre> --seed 0 --direction ccw \
  --launch-arg actuator_model:=true --steer-p-gain 20
```

Ruido y auditoría están activos por defecto; para iterar `--no-gui --real-time-factor 0`
(Obstacle: también `--no-rviz`); validar candidatos con GUI.

## Herramientas (`tools/`)

- `open_standard_suite.sh`: seis campos × dos sentidos; añadir repeticiones.
  usando las 44 rondas registradas; requiere el commit `feb2f46`.
- `check_open_refactor_equivalence.py`: compara con `cf5add4` estados, sensores,
  registros y métricas; necesita el entorno ROS, sin arrancar ROS/Gazebo.
- `view_camera.sh`: cámara y RViz, espera Start y conserva GUI después de DONE.
- `check_obstacle_refactor_equivalence.py`: reproduce trazas Obstacle con `05a0eb3` y el código actual.
- `run_gui_experiment.sh` / `run_obstacle_gui_experiment.sh`, `open_standard_suite.sh`, `run_obstacle_batch.sh`: rondas y lotes.
- `judge_open_runs.py`, `audit_obstacle_runs.py`: re-juicio offline.
