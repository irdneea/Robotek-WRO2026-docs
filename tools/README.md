# tools

Small scripts around the car. None of them is part of what drives it during a round: the strategies live in [`../src`](../src). These scripts prepare the Raspberry Pi, start a round, clean up afterwards and measure the car.

The ones you will use on competition day are the first four.

| Script | What it does | When you use it |
| --- | --- | --- |
| `setup-pi.py` | Installs everything on a fresh Raspberry Pi 5 (Ubuntu 24.04): ROS 2 Jazzy, the packages the code needs, the udev rules and the groups, then builds the workspace. `--check` only reports what is missing, `--dry-run` shows what it would do | Once, when you prepare a Pi |
| `car-run.py open` / `car-run.py obstacle` | Starts a challenge by hand on the car: first stops the autostart and any leftover node, then launches `car.launch.py` with the right profile. Prints a short summary while the round runs | Every test of the Open Challenge, and any custom Obstacle run |
| `obstacle-round.py` | The exact Obstacle command we validated on 12 Nov 2026: starts in the lot, leaves it with the pulses, three laps, partial parallel park. Extra arguments go at the end, for example `direction:=cw` | The Obstacle round |
| `car-clean.py` | Stops every car node that a previous launch left running and sets the motor to zero. A second strategy or a second board driver running next to the new launch once made the car drive into a wall | Before every run (the scripts above call it for you) |
| `car-autostart.py on / off / status / log` | Makes the Pi start the car's launch by itself at boot and wait for the button, so that nobody has to open a terminal at the competition | Optional, once you trust the setup |

Measuring and debugging:

| Script | What it does |
| --- | --- |
| `steer_calibration.py` | Measures the real wheel angle for each servo pulse by driving circles on the floor and reading the gyroscope. The result goes into the wheel table of the car's configuration |
| `open_monitor.py` | Twice a second prints what the Open strategy sees and commands (state, camera line votes, LiDAR distances, gyro, speed and steering). Run it in a second terminal while a round is going |
| `open-debug-run.py` | One Open test without the button that records everything: terminal log, rosbag, CPU use and the telemetry |
| `plot-crash.py` | Plots the file written by the Open crash detector and prints a checklist of possible causes. Needs matplotlib for the figure (`--text` prints only the checklist) |
| `lidar-raw-check.py` | Reads the LD19 directly from its serial port, without the driver, and tells where scans are lost (bad checksums, driver loop timing) |
| `keyboard_racing_connect.py`, `keyboard_racing.py` | Drive the car from the keyboard of a computer, to place it or test the steering. The first sets the car's network and opens the second, which is the window |

Simulation and setup helpers:

| File | What it does |
| --- | --- |
| `install-ubuntu.py` | Installs ROS 2 Jazzy (and Gazebo unless `--no-gazebo`) on Ubuntu 24.04. `setup-pi.py` calls it |
| `make_mat_texture.py` | Draws the texture of the game mat that the simulation uses |
| `robotek_env.py` | Shared helpers of the scripts above (not run on its own) |
| `99-robotek.rules` | udev rules: stable names `/dev/rrc_lite` and `/dev/ldlidar` for the board and the LiDAR, so a different USB order never swaps them. `setup-pi.py` installs it |

The batch labs, comparison tools and bench tests used during development are in [`../development/wro-strategies`](../development/wro-strategies).

All the scripts can be run from the root of the repository (`python3 tools/<name>`). Read the comment at the top of each file: it has the exact usage.
