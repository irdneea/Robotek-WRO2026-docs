# robotek_common

Library (no nodes) shared by the strategies (`robotek_open`, `robotek_obstacle_v3`) and the simulation tools:

- `vehicle.py` — car geometry and sensor mounting (must match `robotek_description`).
- `lidar_odometry.py` — travelled distance from consecutive LiDAR scans (no encoder).

It must not depend on simulation or evaluation packages.
