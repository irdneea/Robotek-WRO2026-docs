# Source code of the vehicle

A ROS 2 Jazzy workspace (`colcon build` from the repository root). Package map and the role of each module of the Obstacle strategy: [docs/03](../docs/03-software-architecture-and-obstacle-strategy.md#1-code-structure).

| Package | What it is |
| --- | --- |
| `robotek_obstacle_v3` | Obstacle Challenge strategy (this is what runs the Obstacle rounds) |
| `robotek_open` | Open Challenge strategy |
| `robotek_hardware` | Adapters between the strategies and the hardware (`base_adapter`, `scan_adapter`, `imu_adapter`, `rear_range`, buttons, LEDs) |
| `rrc_lite_driver`, `rrc_lite_msgs` | Driver of the Hiwonder RRC Lite board |
| `ldlidar_stl_ros2` | LiDAR driver (LDROBOT, MIT) |
| `robotek_course` | Launch files and shared base classes and perception |
| `robotek_common`, `robotek_description` | Measurements of the car and its URDF |
| `robotek_gazebo`, `robotek_evaluation` | Simulator, honest lab and the judge used to test without the car |

Comments in some modules are in Spanish (the team's working language); the docstring at the top of each Obstacle module states in English what it does and why.

Run: `bash tools/obstacle-round.sh` (Obstacle) or `bash tools/car-run.sh open` (Open). Tests: `cd src/robotek_obstacle_v3 && python3 -m pytest test -q`.
