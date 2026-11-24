# tools

Small scripts around the car. None of them is part of what drives it during a round: the strategies live in [`../src`](../src). These scripts prepare the Raspberry Pi, start a round, clean up afterwards and measure the car.

The ones you will use on competition day are the first four.

| Script | What it does | When you use it |
| --- | --- | --- |
| `setup-pi.sh` | Installs everything on a fresh Raspberry Pi 5 (Ubuntu 24.04): ROS 2 Jazzy, the packages the code needs, the udev rules and the groups, then builds the workspace. `--check` only reports what is missing, `--dry-run` shows what it would do | Once, when you prepare a Pi |
| `car-run.sh open` / `car-run.sh obstacle` | Starts a challenge by hand on the car: first stops the autostart and any leftover node, then launches `car.launch.py` with the right profile. Prints a short summary while the round runs | Every test of the Open Challenge, and any custom Obstacle run |
| `obstacle-round.sh` | The exact Obstacle command we validated on 12 Nov 2026: starts in the lot, leaves it with the pulses, three laps, partial parallel park. Extra arguments go at the end, for example `direction:=cw` | The Obstacle round |
| `car-clean.sh` | Stops every car node that a previous launch left running and sets the motor to zero. A second strategy or a second board driver running next to the new launch once made the car drive into a wall | Before every run (the scripts above call it for you) |
| `car-autostart.sh on / off / status / log` | Makes the Pi start the car's launch by itself at boot and wait for the button, so that nobody has to open a terminal at the competition | Optional, once you trust the setup |

Measuring and debugging:

| Script | What it does |
| --- | --- |
| `steer_calibration.py` | Measures the real wheel angle for each servo pulse by driving circles on the floor and reading the gyroscope. The result goes into the wheel table of the car's configuration |
| `open_monitor.py` | Twice a second prints what the Open strategy sees and commands (state, camera line votes, LiDAR distances, gyro, speed and steering). Run it in a second terminal while a round is going |
| `lidar-raw-check.py` | Reads the LD19 directly from its serial port, without the driver, and tells where scans are lost (bad checksums, driver loop timing) |
| `keyboard_racing.py`, `.sh`, `.ps1` | Drive the car from the keyboard of a laptop, to move it around or test the steering. The `.sh` is for macOS and the `.ps1` for Windows |

Simulation and setup helpers:

| File | What it does |
| --- | --- |
| `install-ubuntu.sh` | Installs ROS 2 Jazzy (and Gazebo unless `--no-gazebo`) on Ubuntu 24.04. `setup-pi.sh` calls it |
| `macos_env.sh` | Prepares a macOS terminal (RoboStack) to build the workspace and use RViz against the car |
| `make_mat_texture.py` | Draws the texture of the game mat that the simulation uses |
| `99-robotek.rules` | udev rules: stable names `/dev/rrc_lite` and `/dev/ldlidar` for the board and the LiDAR, so a different USB order never swaps them. `setup-pi.sh` installs it |

All the scripts can be run from the root of the repository (`bash tools/<name>`). Read the comment at the top of each file: it has the exact usage.
