# Obstacle parameters on the car

What each parameter changes and its default. Launch arguments go at the end of the command as `name:=value`. The strategy parameters live in `robotek_obstacle_v3/settings.py` and in the profile `config/car_picam_park_round.yaml`, which `tools/obstacle-round.py` passes with `strategy_params`.

```bash
python3 tools/obstacle-round.py                              # the validated command
python3 tools/obstacle-round.py recover_back:=0.4            # with a launch argument changed
```

## Launch arguments (`car.launch.py`)

| Parameter | Default | Meaning |
| --- | --- | --- |
| `start_lot` | `false` | `true`: the car starts inside the parking lot, against the outer wall and about 1 cm from the rear limit. It reads the direction with the LiDAR, leaves with `lot_exit_steps` and then runs the laps |
| `lot_exit_speed` | `0.2` (round command) | m/s of each pulse of the lot exit |
| `lot_exit_steps` | `L+0.25 R-0.3 L+0.25 R-0.3 L+0.25 R-0.3 C-0.2` (round command) | The exit pulses, separated by spaces: `<side><direction><seconds>`. Side `L` or `R` is full lock (written for counter-clockwise, mirrored in clockwise), `C` is wheels straight. Direction `+` is forward, `-` reverse |
| `recover_back` | `0.3` (round command) | Seconds of reverse at full lock when the car is about to hit something ahead. Each repeat at the same spot adds 0.6 s |
| `motor_rps_per_mps` | `8.0` (round command) | Board rps per m/s with the 1:1 gearing |
| `motor_min_rps` | `2` (round command) | Minimum rps while moving: the motor does not start the car much below that (about 0.25 m/s) |
| `motor_max_rps` | `auto` (4 for the Obstacle) | Cap on rps |
| `rear_range` | `auto` | The VL53L0X rear distance sensor |
| `camera_driver` | `picam` for the Pi camera | The camera node |
| `strategy_params` | `auto` | YAML file with more strategy parameters |
| `button`, `gpio_button` | `true` | The board button (and the GPIO 16 button) start the round |

## Strategy parameters (`settings.py`)

| Parameter | Default | Meaning |
| --- | --- | --- |
| `cruise_speed`, `pillar_speed`, `finish_speed` | 0.28, 0.30, 0.15 | m/s on a free lane, near a sign, and on the last metres |
| `front_speed` | 0.20 | Speed cap with something close ahead |
| `steer_limit` | 0.307 (0.3054 in the profile) | Maximum wheel angle, rad (17.5 to 17.6°) |
| `pillar_clearance` | 0.18 | m from a sign's box to the side of the car when passing it |
| `pillar_lookahead` | 1.8 | m ahead at which the car starts changing side for a sign |
| `park` | 0 (the profile sets 1) | Park after the three laps |
| `park_mode` | 0 (the profile sets 1) | 1 is the fixed manoeuvre closed on sensors |
| `park_fixed_partial` | 0 (the profile sets 1) | Partial park: approach, entry and straight into the lot, then the finishing pulses |
| `park_finish_steps` | profile | Finishing pulses: `C+0.20 R-0.40 L-0.50 R+0.05 L-0.15 R+0.1 L-0.1` |
| `park_lot_length`, `park_lot_end`, `park_lot_depth` | 0.3675, 0.31 (profile), 0.20 | The lot of our team field (length 1.5 × the car), far limit position and depth |
| `steer_watch` | 1 | Stop and centre the wheels when full lock gives no turn on the gyro |
| `scan_max_age`, `imu_max_age` | 0.35 s, 0.20 s | Older LiDAR or gyro data brake the car |

## Constants in the code

| Constant | Value | File | Meaning |
| --- | --- | --- | --- |
| `RECOVER_LOOK` | 0.18 m | `mission.py` | Distance along the arc the car is driving that must be free; if something ahead falls in it, the car brakes |
| `RECOVER_NOSE` | 0.05 m | `mission.py` | Only the front of the car counts, so passing a sign close by does not trigger it |
| `RECOVER_BRAKE` | 0.2 s | `mission.py` | Dead stop (`/robotek/estop`) before reversing |
| `RECOVER_REPEAT`, `RECOVER_STRAIGHT` | 0.3 m and 8 s, 0.6 s | `mission.py` | A recover within 0.3 m and 8 s of the last is a repeat and adds 0.6 s of reverse, up to 3 times |
| `SEAT_HITS` | 2 | `mission.py` | Sightings before a seat counts as a sign |
| `HOLD` | 0.15 units | `mission.py` | Distance before and after a sign where its side offset is held |
| `CAMERA_MAX_AGE` | 0.8 s | `strategy.py` | An older camera frame stops the car (LiDAR and gyro: 0.35 s) |
| `PRESTEER_S`, `SETTLE_S` | 0.5 s, 0.4 s | `lot_exit.py` | Before each pulse the wheels turn with the car stopped; after it the car stands still |
| `REAR_STOP_MM` | 20 mm | `lot_exit.py` | When reversing, a rear reading under this brakes dead |

## Rear sensor (`rear_range`)

| Parameter | Default | Meaning |
| --- | --- | --- |
| `correct` | `true` | `false` publishes the raw reading without the correction table |
| `table_raw_mm`, `table_mm` | `[70, 75, 77, 83, 96, 138, 231, 476]`, `[10, 20, 30, 40, 50, 85, 170, 420]` | Raw to real millimetres, measured against a wall; slope 1 beyond the table |
