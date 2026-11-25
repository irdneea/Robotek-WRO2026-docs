# The code of the car

This is a ROS 2 Jazzy workspace. Build it from the root of the repository with `colcon build`, or let `tools/setup-pi.py` do everything on the Raspberry Pi.

The best way in is to follow one command through the system. A strategy decides a **speed and a steering angle**; everything else in the workspace either brings it the data to decide, or turns its answer into signals for the motor and the servo.

```
LiDAR ─► scan_adapter ─┐
Camera ────────────────┤
IMU ─► imu_adapter ────┼─► strategy node ─► /cmd_vel_raw ─► base_adapter ─► servo + motor
Rear ToF ──────────────┤   (decides)                          (converts)      (RRC Lite board)
Button ─► start_button ┘
```

The same strategy code also runs in the simulator and in the lab, because it never touches ROS or the hardware itself.

## What to read, in order

1. **The decisions.** One file per challenge holds the whole logic:
   * Obstacle: `robotek_obstacle_v3/robotek_obstacle_v3/mission.py`
   * Open: `robotek_open/robotek_open/v5/mission.py`
2. **How the decisions reach the hardware.** `drive.py` (Obstacle) and `v5/node.py` (Open) wire the mission to ROS; `robotek_hardware/base_adapter.py` turns the command into servo microseconds and motor speed.
3. **The rest**, as you need it, from the tables below.

## Packages

| Package | What it is | Runs on the car |
| --- | --- | :-: |
| [`robotek_obstacle_v3`](robotek_obstacle_v3) | Obstacle Challenge strategy: signs, lot exit, parking | yes |
| [`robotek_open`](robotek_open) | Open Challenge strategy (version 5) | yes |
| [`robotek_hardware`](robotek_hardware) | Nodes between the strategies and the hardware: adapters, button, LEDs, cameras, rear sensor | yes |
| [`rrc_lite_driver`](rrc_lite_driver), [`rrc_lite_msgs`](rrc_lite_msgs) | Driver and messages of the Hiwonder RRC Lite board (motor, servo, IMU, button, LEDs) | yes |
| [`ldlidar_stl_ros2`](ldlidar_stl_ros2) | Driver of the LDROBOT LD19 LiDAR (third-party, MIT) | yes |
| [`robotek_common`](robotek_common) | Measurements of the car and LiDAR odometry, shared by both strategies | yes |
| [`robotek_description`](robotek_description) | The car as a URDF model with its STL meshes (used by RViz and Gazebo, and as the reference for the measurements) | yes |
| [`robotek_course`](robotek_course) | Launch files (`car.launch.py` starts everything on the car), the base classes of the strategies and the round referee | yes |
| [`robotek_gazebo`](robotek_gazebo) | The field for Gazebo Harmonic | simulation only |
| [`robotek_evaluation`](robotek_evaluation) | The judge, the contact recorder and the fast labs used to test without the car | simulation only |

Rule of the workspace: the two strategies depend only on `robotek_common`. They never import anything from the simulation packages, so nothing they use exists only in the simulator.

## Obstacle: `robotek_obstacle_v3/robotek_obstacle_v3/`

| File | What it does |
| --- | --- |
| `mission.py` | The state machine: SETUP, LOT_EXIT, RUN, PARK, STOP. Sign memory, choice of side, line planning, steering law, speed rules, recoveries |
| `settings.py` | Every parameter you may want to change, with its default and a comment. They are also ROS parameters |
| `drive.py` | The ROS node: reads the sensors, finds the colour blobs in the camera, pairs them with LiDAR clusters, calls the mission and publishes the command |
| `strategy.py` | Wraps the mission: stops the car when a sensor is stale and ends the round at 180 s |
| `perception.py` | Finds sign-sized clusters in a LiDAR scan |
| `localizer.py` | Works out the car's position in the lane by fitting the LiDAR points to the known walls |
| `field.py`, `scene.py` | The geometry of the field in the frame the mission uses, and the immutable observation handed to it each tick |
| `corner.py`, `corner_table.py` | Plans the line through a corner (straight, arc, straight), scoring each candidate by driving it in a small simulation; the table holds the answers already computed |
| `lot_exit.py` | Leaves the parking lot with a short sequence of pulses |
| `park_fixed.py`, `park.py`, `parking_search.py` | Parallel parking: the fixed manoeuvre closed on sensors (the one that is used), the planned version and the search for the lot |
| `steer_watch.py` | Notices when the servo does not follow a full-lock command and stops the car for a moment |
| `car.py` | Dimensions of the car and the camera, as the strategy was tuned with them |
| `recording.py` | What every round leaves in `~/runs`: telemetry, events, parameters |
| `config/` | The YAML profiles. `car_picam_park_round.yaml` is the one of the validated round |

Chapter 5 and chapter 6 of the main [README](../README.md) explain what these files do and why.

## Open: `robotek_open/robotek_open/`

| File | What it does |
| --- | --- |
| `v5/mission.py` | The state machine: SETUP, FOLLOW, TURN, FINISH, STOP. Heading law, corner detection and the stop |
| `v5/node.py` | The ROS node: LiDAR, gyroscope and camera in, command out |
| `v5/settings.py` | Parameters of the node, with the defaults of the real car |
| `v5/scene.py` | What the LiDAR tells the strategy, as four numbers per scan |
| `v5/crash_watch.py` | Optional detector that notices a collision (off by default) |
| `v5/recording.py`, `open_recording.py` | Telemetry of the round |
| `open_vision.py` | Reads the direction of the first turn from the blue and orange lines on the mat |
| `open_constants.py` | The few constants that are not strategy parameters (LiDAR position, control rate) |
| `config/car_picam.yaml` | The speeds and gains of the real car |

## Hardware: `robotek_hardware/robotek_hardware/`

| File | What it does |
| --- | --- |
| `base_adapter.py` | Turns a speed and a wheel angle into motor speed and servo microseconds, with the measured wheel table, limits and ramps |
| `scan_adapter.py` | Rotates the LiDAR scan so that 0 rad is straight ahead and cuts what the car cannot use |
| `imu_adapter.py`, `imu_axes.py` | Puts the board's IMU axes in the car frame (x forward, y left, z up), and a tool to find them |
| `start_button.py`, `gpio_button.py` | The Start: the board button or the button on the Pi's GPIO 16 |
| `rear_range.py` | The VL53L0X rear distance sensor over I²C, calibrated against a ruler |
| `pi_camera_publisher.py`, `camera_publisher.py` | The Pi camera (CSI) and an optional USB camera |
| `battery_guard.py` | Warns when the battery is low; it never stops the car |
| `status_leds.py`, `status_colors.py` | Shows the car's state on the two RGB LEDs of the board |
| `mapping.py` | The unit conversions (m/s to motor rps, wheel angle to servo microseconds), without ROS so that they can be tested |
| `servo_steer.py` | Small node that moves only the steering servo, for bench tests |

The wiring and the calibration of each of these are in [`robotek_hardware/README.md`](robotek_hardware/README.md).

## Launch files: `robotek_course/launch/`

| File | What it starts |
| --- | --- |
| `car.launch.py` | Everything on the car: the hardware nodes and the strategy. Normally started through `tools/car-run.py` |
| `sim.launch.py` | The simulator: Gazebo, the field, the car and its sensors |
| `round.launch.py`, `obstacle_round.launch.py` | A scored round in the simulator, with the referee |

## Tests

```bash
cd src/robotek_obstacle_v3 && python3 -m pytest test -q     # 45 tests with ROS (without ROS: 40 pass, 1 is skipped)
cd src/robotek_open && python3 -m pytest test -q            # 62 tests
cd src/robotek_hardware && python3 -m pytest test -q        # conversions, wiring checks (need ROS for some)
```

Run the car with `python3 tools/obstacle-round.py` (Obstacle) or `python3 tools/car-run.py open` (Open). More in chapter 9 of the [README](../README.md#9-build-run-and-test-it-yourself).
