# robotek_open

Estrategia del **Open Challenge**: el **v5** (nodo `open_strategy`, ejecutable `open_strategy_v5`). Es la única
estrategia del Open: el v1–v4 se borraron el 26 oct 2026 (sus rondas siguen en `docs/open-challenge-runs/` y su
código en la historia de git, hasta el commit `2b17266`). Depende solo de `robotek_common` (odometría LiDAR
`lidar_odometry.py`, medidas del coche `vehicle.py`); la preparación y el análisis de rondas están en
`robotek_evaluation`.

## Solo sensores

El nodo usa `/scan`, el giroscopio de `/imu` y `/camera/image`. `/start` inicia la ronda y `/clock` aporta el reloj
de simulación; publica `/cmd_vel` y la imagen de diagnóstico `/camera/direction_debug`. No se suscribe a odometría,
pose de Gazebo ni articulaciones, y no lee la orientación absoluta de la IMU. El grabador `audit_pose_recorder`
recibe esos datos por separado para el juez y los márgenes.

| Archivo | Responsabilidad |
|---|---|
| `v5/scene.py` | `Scene`: lo que el LiDAR dice en cada escaneo (paredes a los lados, eje frontal, fin de la isla) |
| `v5/mission.py` | `OpenMission` y `Params`: estados, rumbo, giros y parada |
| `v5/node.py` | `OpenV5Node`: conexión ROS y ciclo de control |
| `v5/settings.py` | Parámetros ROS del nodo (misión, operación y cámara) y su validación |
| `v5/recording.py` | Telemetría de la misión en el CSV que leen el runner, el juez y los informes |
| `open_vision.py` | `OpenVision`: sentido de la pista por las líneas azul y naranja |
| `open_recording.py` | Escaneos, eventos y evidencia de la cámara |
| `open_mission_clock.py` | Reloj de la ronda (simulación o pared) |
| `open_constants.py` | Constantes de hardware y sensores que se guardan con cada ronda |
| `open_profile.py` | Carga y validación de perfiles |
| `config/open_v5.yaml` | Perfil activo |

La distancia siempre proviene de LiDAR y el rumbo del giroscopio calibrado.

```bash
colcon build
bash src/robotek_evaluation/tools/run_gui_experiment.sh prueba-open \
  --params-file src/robotek_open/config/open_v5.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction ccw --controller-direction auto --spawn-x 0.0 --spawn-y -1.15 --spawn-yaw 0.0 \
  --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 [--no-gui --real-time-factor 0]
```

Para iterar se permite `--no-gui --real-time-factor 0`; validar los candidatos con GUI. Cada intento conserva
parámetros, constantes, código, `round.json` y su entrada en `rounds.jsonl`. Los tiempos desde Start incluyen la
calibración y la detección del sentido; las vueltas son parciales; los puntos son estimados y el bonus provisional.

Pruebas: `test_v5_scene.py`, `test_v5_mission.py`, `test_open_vision.py`, `test_open_recording.py`,
`test_mission_clock.py`. Cómo funciona por dentro: [learn/03-open-strategy](../../learn/03-open-strategy/README.md).
