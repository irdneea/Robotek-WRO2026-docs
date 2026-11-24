# robotek_gazebo

The field of the WRO 2026 Open Challenge for **Gazebo Harmonic** (gz-sim 8) and the bridge to ROS 2. The car itself is in `robotek_description`.

```
robotek_gazebo/
├── worlds/        robotek_open_field.sdf (the default field) and seven lane-width variants
│                  (square100, square180, rect100x180, rect180x100, shift140, east140x100, ...)
├── models/robotek_game_mat/   the mat; its texture is drawn by tools/make_mat_texture.py
├── config/        robotek_bridge.yaml: the topics that cross between Gazebo and ROS 2
└── launch/        robotek_sim.launch.py: Gazebo + bridge + car
```

The fields carry a contact sensor (`wall_contact`) on the walls: the judge uses it to know whether the car touched them.

You normally do not launch it directly: use `ros2 launch robotek_course sim.launch.py` (the simulator) or `ros2 launch robotek_course round.launch.py` (a scored round).
