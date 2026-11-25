# robotek_bringup

Launch que combinan simulación, estrategia y evaluación:

- `open_challenge.launch.py` — Gazebo (`robotek_gazebo`) + `open_strategy` + auditoría/servo estimado.
- `obstacle_challenge.launch.py` — Gazebo con pilares + `obstacle_strategy` + auditoría/servo estimado.

- `robot.launch.py` — **robot real**: drivers (RRC Lite, LiDAR, cámara) + `robotek_hardware` +
  la estrategia (`challenge:=open|obstacle`, `mode:=park`), sin simulación ni juez. Incluye
  `battery_guard`: con la batería bajo 6,6 V (`battery_min_v`) detiene el coche (`battery_guard:=false` lo apaga).

Los runners de `robotek_evaluation/tools` llaman a los launch de simulación.
