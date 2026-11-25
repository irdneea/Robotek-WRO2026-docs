# robotek_hardware

This package is only for the **real car** (Raspberry Pi). It connects a strategy to the hardware of our car. The strategy node reads `/scan`, `/imu`, the camera image and `/start`, and publishes a `Twist` on `/cmd_vel_raw`, exactly as it does in the simulator. The nodes here translate those names to the Hiwonder RRC Lite board (servo, motor, IMU, button, LEDs) and to the LD19 LiDAR, and back, so the strategy code does not change between the simulator and the car.

```
LD19 LiDAR      -> /scan (driver)       -> scan_adapter -> /robotek/scan  (0 rad ahead, ±110°)   -> strategy
RRC Lite IMU    -> /rrc/imu_raw         -> imu_adapter  -> /robotek/imu   (x ahead, y left, z up) -> strategy
Camera          -> /picam/image_raw/compressed (or /usb_cam/image_raw)                           -> strategy
RRC Lite button -> start_button -> /start (first press), /robotek/stop (any other press)
strategy /cmd_vel_raw -> base_adapter -> servo (microseconds, /rrc/acker_servo/set_state)
                                      -> motor (board rps, /rrc/set_motor, port M2)
```

Everything is started with one launch file, `ros2 launch robotek_course car.launch.py strategy:=<package>` (see "Launching on the car").

## Nodes

| Node | What it does |
| --- | --- |
| `base_adapter` | Turns `/cmd_vel_raw` into servo microseconds (through the measured wheel table, capped at 25°) and into motor rps for `/rrc/set_motor`. It limits acceleration (`accel_limit`) and deceleration (`decel_limit`), stops the motor if commands stop arriving (`watchdog`) and stops it dead on `/robotek/estop` |
| `scan_adapter` | Takes the LD19 scan (its zero points backwards) to `/robotek/scan` with 0 rad ahead, and discards what the car cannot see (beyond ±110° the rays hit the chassis) |
| `imu_adapter` | Rotates the board's IMU into car axes (x ahead, y left, z up). The strategies integrate the gyro z, so the axes must be right |
| `start_button` | The first press of the board button publishes `/start` (and beeps), any later press publishes `/robotek/stop` and the car stays stopped until the next launch |
| `gpio_button` | A push button on GPIO 16 of the Pi (other leg to GND, internal pull-up) → `/robotek/gpio_button` |
| `rear_range` | VL53L0X distance sensor on the Pi's I²C bus (0x29, bus 1) → `/robotek/rear_range` (metres) and `/robotek/rear_range_mm` (millimetres, `-1` when it sees nothing) |
| `battery_guard` | If the board's battery (`/rrc/battery`) is under 6.8 V for 5 readings in a row, it makes the LEDs blink red. It never stops the car |
| `status_leds` | The two RGB LEDs of the board: green = ready for the button, blue = pressed (round running, finished or stopped), blinking red = low battery |
| `imu_axes` | Calibration tool: with the car still and a push forward, it prints the axes for `imu_adapter` |
| `camera_publisher` | USB camera (YUYV 640×480, 15 fps) to `/usb_cam/image_raw`; it finds the camera by itself and retries if it is missing |
| `pi_camera_publisher` | Pi camera (IMX708, wide lens) through `rpicam`: publishes the JPEG frames the strategies read |
| `servo_steer` | Bench test: an angle (`Float32`, rad, + left) moves **only the servo**, never the motor |

The pure logic (servo and motor conversions, acceleration limits, IMU axes, LED colours) is in `mapping.py` and `status_colors.py` and is tested without hardware.

## Preparing the Pi (one command)

The car's computer is a Raspberry Pi 5 with Ubuntu 24.04 and ROS 2 Jazzy. On a fresh Pi with Ubuntu 24.04 (arm64) and internet:

```bash
git clone https://github.com/ilovmangos/Robotek-WRO2026.git
cd Robotek-WRO2026
python3 tools/setup-pi.py            # installs, configures and builds; asks for sudo when needed
python3 tools/setup-pi.py --check    # afterwards: only checks (board, LiDAR, camera, groups); changes nothing
```

`setup-pi.py` can be run again (it skips what is done) and `--dry-run` shows the commands without running them. It, in order:

1. checks that the system is Ubuntu 24.04;
2. installs ROS 2 Jazzy **base** (no Gazebo or RViz) and the apt packages of the car (`cv_bridge`, `robot_state_publisher`, `xacro`, `tf2_ros`, `python3-serial`, `python3-lgpio`, `python3-opencv`, `v4l-utils`, ...);
3. installs the udev rules `tools/99-robotek.rules` (stable names `/dev/rrc_lite` and `/dev/ldlidar`, permissions) and adds you to the groups `dialout`, `video` and `gpio` (log out and in again);
4. builds everything with `colcon build --symlink-install`.

> **Safety: the first time, put the car on supports (wheels in the air).** Neither `setup-pi.py` nor the launch moves the motor by itself: the motor only moves when a strategy publishes `/cmd_vel_raw`, and the strategy waits for Start (the board button). Even so, `base_adapter` limits acceleration (1 m/s²), never asks for more than `motor_max_rps`, a 0.3 s watchdog stops it if commands stop, the steering is limited to `wheel_limit_deg` (19°), and a second press of the button (`/robotek/stop`) holds it stopped until the next launch. `/robotek/estop` (a `Bool`, true) also stops it. If the motor keeps turning anyway, switch the board off.

## Third-party code included in the repository

The car needs pieces that **this repository did not write**. They are all in `src/`, so `git clone` plus `colcon build` is enough.

| Piece | Purpose | Origin | Licence |
| --- | --- | --- | --- |
| `src/ldlidar_stl_ros2` | Driver of the LDROBOT LD19 LiDAR: publishes `/scan` | [ldrobotSensorTeam/ldlidar_stl_ros2](https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2), commit `bf668a8` | MIT (Copyright 2020 SHENZHEN LDROBOT CO., LTD.). Licence and notices intact; only the two build fixes of `patches/ldlidar_stl_ros2-build.patch`, already applied (see its `NOTICE-ROBOTEK.md`) |
| `src/rrc_lite_driver`, `src/rrc_lite_msgs` | Driver of the RRC Lite board (IMU, button, battery, LEDs, steering servo, motor) | Based on `driver/ros_robot_controller` and `driver/ros_robot_controller_msgs` from [Hiwonder/MentorPi](https://github.com/Hiwonder/MentorPi) | The original code declares no licence. It is included with Hiwonder's permission; the team's changes are MIT |
| `camera_publisher`, `pi_camera_publisher` | Cameras | Team code | MIT |

Changes of the team with respect to MentorPi:

1. Names: `ros_robot_controller` became `rrc_lite_driver` (node `rrc_driver`), its messages `rrc_lite_msgs`, and topics became `/rrc/...`.
2. A new message `SetAckerServoState` (`float64 duration`, `uint16 position` in microseconds) and a subscriber `/rrc/acker_servo/set_state` that moves the steering servo (`acker_channel`; on our car it is channel 1 = connector J4).
3. The serial port is the parameter `port`; empty (the default) means `/dev/rrc_lite` or `/dev/ttyACM0`.
4. With no board plugged in, the node does not crash: it warns and retries every 3 s. If the USB drops **during** a round the node dies and the car has to be relaunched; this happened on 4 Nov 2026 from electrical noise (`disabled by hub (EMI?)` in the kernel log).
5. Servo offsets (`config/servo_config.yaml`) are read from the installed package.
6. `motor_type` (in `controller_params.yaml`) is **−1 on our car: it is not sent**. With type 2 the motor ran away (see Motor).
7. `/rrc/reset` (`std_msgs/Empty`) resets the board through the RTS line of its USB chip, and 2.5 s later prepares it again. It was the old brake of `base_adapter` (`brake_reset`), switched off since 8 Nov.

## Hardware: device names and permissions

* **RRC Lite board**: appears as `/dev/ttyACM0` (USB `1a86:55d4`); the udev rule adds the stable name `/dev/rrc_lite`. Your user must be in the `dialout` group.
* **LD19 LiDAR**: CP210x adapter (USB `10c4:ea60`), `/dev/ttyUSB0` at 230400 baud, the port `ld19.launch.py` opens; the udev rule adds `/dev/ldlidar`.
* **Motor**: a Hiwonder JGA27-310R encoder motor (20:1 gearbox, 450 rpm) on port **M2** of the RRC Lite (`rrc_motor_port: 2`), with no motor type sent.
* **Cameras**: the Pi camera (IMX708 wide) through `rpicam`; a USB camera is still supported (`camera_driver:=usb_cam` or the team's `camera_publisher`, which picks the first `/dev/v4l/by-id/*-video-index0` because the `/dev/videoN` numbers change on the Pi 5).

The udev rules only use USB identifiers that were confirmed: `1a86:55d4` for the board and `10c4:ea60` for the LiDAR.

## Launching on the car

```bash
source install/setup.bash
ros2 launch robotek_course car.launch.py strategy:=robotek_obstacle_v3 start_lot:=true    # or use tools/obstacle-round.py
```

Wait until the board LEDs turn **green** (the strategy is waiting for the button), place the car at its start and press the button once: that is Start (`/start`) and the LEDs turn blue. Press again to stop: the motor stays at 0 until you launch again. `ros2 launch robotek_course car.launch.py --show-args` lists the options (`motor_max_rps:=`, `strategy_params:=<file.yaml>`, `camera_driver:=`, `rear_range:=`, `battery_guard:=false`, ...). If a device is missing the launch says so and carries on, so the stack can be tried on a laptop; each node warns clearly and retries without moving anything.

### Motor: speed and braking

`base_adapter` converts the strategy's speed like this:

* **Motor**: `rps = v · motor_rps_per_mps`, with the sign `rrc_motor_sign`, limited to `motor_max_rps`.
  * Configuration since 8 Nov 2026: JGA27-310R on **M2**, no motor type sent (`motor_type: -1`).
  * With the first gearing (54:30), `motor_rps_per_mps` was **4.4**, measured with the LiDAR: 0.15 / 0.30 / 0.50 m/s asked gave 0.16 / 0.28 / 0.45 with a factor of 4.0, so the factor became 4.4. Since 12 Nov the gearing is 1:1 and the default is **7.0** (the Obstacle command uses 8.0).
* **Stopping**: a plain 0. The car coasts 8–35 cm (with 54:30) and stays still. `brake_reset` and `brake_rps` are off. They were patches from 1–4 Nov, when motor type 2 was being sent: the RRC Lite firmware has **negative** PID gains for that motor type, and our motor's encoder counts the other way from Hiwonder's, so the board's loop pushed the wrong way (full PWM for any set point, not stopping at 0, sometimes reversing). Without a motor type the board uses its own default and controls well.
* **Low speed**: this motor has little torque at the start; at full steering lock from standstill it does not start below about 1 rps (about 0.23 m/s). Three adapter options, off by default, help: `motor_min_rps` (every move command asks at least this; the Obstacle round uses 2, i.e. about 0.25 m/s), `motor_kick_rps` / `motor_kick_s` (a stronger start) and `motor_pulse_rps` / `motor_pulse_period_s` (alternate that value and 0 so the average matches the command). Even pulses of 1 rps every 2 s did not move the car at full lock (8 Nov 2026).
* **Acceleration**: `accel_limit` 1 m/s² (soft start). When stopping, `decel_limit` 0.6 m/s².
* **Steering**: the wheel angle of the `Twist` goes through the `wheel_table_*` table to the servo (µs) and is limited to `wheel_limit_deg` (19°). The table was measured on 1 Nov 2026 (`servo_measured: true`). The strategies ask for less: 17.6° (Open) and 17.5° (the Obstacle's profile). As soon as the strategy publishes, even while it waits for Start, the servo goes to the centre.
  * **An intermittent failure we are still watching**: sometimes the board receives full lock and the car goes straight on (gyro near 0). It happened in two Open rounds of 4 Nov, two of 8 Nov and one Obstacle round. The servo works when tested alone; on 18 Nov its mounting on the car was found to be wrong. The Obstacle has a steering watch for it (see chapter 6 (RUN) of the main README).
* **Board resets**: the gyro goes quiet for about 2.5 s ("Board data back after … s"), mostly when the car is jammed and pushing. `rrc_driver` resends the servo offsets afterwards.

### From the button to the motor

`board button → rrc_driver (/rrc/button) → start_button → /start → strategy node`. The strategy prints `Start`, and its state (`/robotek/state`, transient local, read by `status_leds`) goes from `WAIT_START` to `CALIBRATE` and `DETECT_DIRECTION`. The command comes back as `/cmd_vel_raw → base_adapter → servo + /rrc/set_motor → rrc_driver`. A second press publishes `/robotek/stop`: the strategy goes to `OPERATOR_STOP` and `base_adapter` holds the motor at 0. On the car `use_sim_time` is false, the node uses wall-clock time. Note that on the Pi the 50 Hz control timer runs at about 35–40 Hz, so a node that integrates the gyro with a fixed 1/50 s gets a heading that is too short; the Open v5 uses the real time between cycles. If the LiDAR (0.35 s) or the gyro (0.2 s) stop arriving, the log says `A sensor went quiet: braking until it is back` and the speed is 0.

## Calibration

All values are in [`config/robot.yaml`](config/robot.yaml). They are the ones of our car; **measure your own** before trusting them.

* **Steering servo** (`base_adapter`): centre (`servo_center_us`, 1403 µs), gains (`servo_gain_pos`, `servo_gain_neg`, 20 µs per servo degree), direction (`servo_sign`) and the `wheel_table_*` table (the real wheel angle for each servo angle, measured by driving circles). Test the servo alone with `ros2 run robotek_hardware servo_steer` and publishing on `/steer`.
* **Motor** (`rrc_motor_port`, `rrc_motor_sign`, `motor_rps_per_mps`, `motor_max_rps`) and `motor_type` in `src/rrc_lite_driver/config/controller_params.yaml`. If you change the port or the type, check the direction again. Measure the speed with the LiDAR (distance to a wall before and after) with short pulses.
* **Wheelbase** (`wheelbase`): must match `WHEELBASE` in `robotek_common/vehicle.py`.
* **IMU axes** (`imu_adapter`): with the Pi and the board mounted the axes change. With the car still, run `ros2 run robotek_hardware imu_axes`, push it forward, copy the block it prints into `robot.yaml` and set `measured: true`.
* **LiDAR** (`scan_adapter`): `angle_offset` (π for the LD19 mounted with the cable at the back) and `reverse` if your driver's angles grow clockwise. Check in RViz: a wall ahead must appear ahead.

## Tests without hardware

```bash
cd src/robotek_hardware && python -m pytest
```

They test the conversions of `mapping.py` and the colours of `status_colors.py`, without a board and almost all without ROS (the `imu_axes` test needs the ROS environment and is skipped without it). With ROS loaded you may need `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` so that `pytest` does not load the `launch_testing` plugins.

## Licence

MIT for the code of this package, including `camera_publisher` and the team's changes in `rrc_lite_driver` / `rrc_lite_msgs`. `src/ldlidar_stl_ros2/` is a copy of the LDROBOT driver, also MIT (its licence and notices untouched). The Hiwonder code in `rrc_lite_*` declares no licence and is included with Hiwonder's permission.
