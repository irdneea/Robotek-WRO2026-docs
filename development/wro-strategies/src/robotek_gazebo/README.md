# robotek_gazebo

Gazebo (**Harmonic / gz-sim 8**) simulation assets for the **Robotek** vehicle —
a ROS 2 Jazzy package providing the **WRO 2026 Future Engineers game field**.
The car itself (URDF/xacro) lives in `robotek_description`, shared with the real robot.

## Contents

```
robotek_gazebo/
├── package.xml
├── CMakeLists.txt
├── worlds/
│   ├── robotek_game_field.sdf     # Obstacle Challenge (traffic signs + parking)
│   └── robotek_open_field.sdf     # Open Challenge (no obstacles)
├── models/
│   └── robotek_game_mat/          # textured mat floor (from the playfield PDF)
│       ├── model.config
│       ├── model.sdf
│       └── materials/textures/playfield.png
├── config/
│   └── robotek_bridge.yaml        # ros_gz_bridge topics
└── launch/
    └── robotek_sim.launch.py          # Gazebo + ROS 2 bridge + spawn
```

## Worlds

Both worlds use a 1000 mm corridor and share the same floor, walls and start
zone. Values from `docs/WRO-2026-Future-Engineers-Gamefield-Specifications.md`:

| Element | Value |
|---|---|
| Game mat | 3.20 × 3.20 m (3200 × 3200 mm) |
| Driving area | 3.00 × 3.00 m (3000 × 3000 mm) |
| Corridor | 1.00 m |
| Exterior / interior wall height | 100 mm (black) |
| Starting zone | 500 × 200 mm |

| World | `field:=` | Contents |
|---|---|---|
| `worlds/robotek_game_field.sdf` | `obstacle` (default) | mat, walls, start zone, **8 dynamic traffic signs**, **parking lot** |
| `worlds/robotek_open_field.sdf` | `open` | mat, walls, start zone — **no obstacles** |

Model names: `ground_plane`, `game_mat` (textured floor), `game_field` (walls,
start zone, parking lot) and, in the obstacle world, `traffic_signs`.

### Floor / game mat

The mat floor is the `robotek_game_mat` model: a static 3.2 × 3.2 m plate whose
top face is textured with the official playfield artwork. The texture
`materials/textures/playfield.png` (4096 × 4096) is rendered from
`docs/WRO-2026_FutureEngineers_Playfield.pdf` at the PDF TrimBox (3200 mm).

Because it is referenced as `model://robotek_game_mat`, the launch file sets
`GZ_SIM_RESOURCE_PATH` to this package's `models/` directory. If you run
`gz sim` directly, set it yourself:

```bash
export GZ_SIM_RESOURCE_PATH="$(ros2 pkg prefix robotek_gazebo)/share/robotek_gazebo/models"
```

## Vehicle model (`robotek_description/urdf/robotek.urdf.xacro`)

A simplified **Ackermann** car, sized from the team's STLs (`Robotek-WRO2026/models/`):

| Part | Size |
|---|---|
| Chassis plate | 177 × 90 × 30 mm |
| Wheels | Ø60 mm, 12 mm wide |
| Wheelbase / track | 130 mm / 100 mm |

- **Drive:** `gz-sim-ackermann-steering-system` (rear-wheel drive, front steering,
  `±25°` (`±0.436332 rad`) steering limit).
- **Sensors:** 360-beam lidar, front camera (640×480), IMU.
- **TF:** `robot_state_publisher`, fed by bridged `/joint_states`.

Bridged topics (`config/robotek_bridge.yaml`):

| ROS topic | Direction | Source |
|---|---|---|
| `/cmd_vel` | ROS → GZ | Ackermann command (`/model/robotek/cmd_vel`) |
| `/odom` | GZ → ROS | Ackermann plugin |
| `/joint_states` | GZ → ROS | joint-state publisher (→ `robot_state_publisher`) |
| `/scan`, `/imu`, `/camera/image` | GZ → ROS | lidar, IMU, camera |
| `/clock` | GZ → ROS | set `use_sim_time:=true` on your nodes |

## Build

From the workspace root (this repository):

```bash
colcon build --packages-select robotek_gazebo
source install/setup.zsh
```

## Run

`robotek_sim.launch.py` uses `ros_gz_sim` and starts `ros_gz_bridge` (bridges
`/clock` by default — see `config/robotek_bridge.yaml`), and can spawn a robot
model:

```bash
ros2 launch robotek_gazebo robotek_sim.launch.py                 # spawns robotek_description's URDF
ros2 launch robotek_gazebo robotek_sim.launch.py field:=open
ros2 launch robotek_gazebo robotek_sim.launch.py gui:=false
ros2 launch robotek_gazebo robotek_sim.launch.py spawn:=false    # world only, no robot
ros2 launch robotek_gazebo robotek_sim.launch.py robot:=/path/to/other.urdf
```

Add your robot's topics (cmd_vel, odom, scan, tf, camera, …) to
`config/robotek_bridge.yaml`, and set `use_sim_time:=true` on your own nodes so
they follow the bridged `/clock`.

## Notes

- `robotek_sim.launch.py` requires `ros_gz_sim` +
  `ros_gz_bridge` (`sudo apt install ros-jazzy-ros-gz`).
- The world is `start_paused` in the GUI; press Play, or launch with `-r`
  (the launch file already passes `-r`).
- Regenerate the mat texture from the PDF with PyMuPDF: render the page
  TrimBox to a 4096 × 4096 PNG and save it to
  `models/robotek_game_mat/materials/textures/playfield.png`.
