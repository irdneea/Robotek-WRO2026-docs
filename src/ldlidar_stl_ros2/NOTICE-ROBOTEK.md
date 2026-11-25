# Provenance of this copy

This folder is a copy of the driver of the LDROBOT LD19 LiDAR (and LD06 / STL27L), included here so that `git clone` plus `colcon build` is enough on the Raspberry Pi.

* Origin: https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2, commit `bf668a89baf722a787dadc442860dcbf33a82f5a` (8 May 2023, "Update README.md").
* Licence: MIT, Copyright (c) 2020 SHENZHEN LDROBOT CO., LTD. The `LICENSE` file and the copyright notices of every file are untouched.
* Changes with respect to the original:
  1. Two build fixes for Ubuntu 24.04 / ROS 2 Jazzy (`../robotek_hardware/patches/ldlidar_stl_ros2-build.patch`, already applied): `find_package(Threads)` and `Threads::Threads` in `CMakeLists.txt`, and `#include <pthread.h>` in `ldlidar_driver/src/logger/log_module.cpp`.
  2. On systems that are not Linux (macOS, simulation only) `CMakeLists.txt` builds nothing, so that `colcon build` does not fail there.
  3. **A change of behaviour by the team (11 Nov 2026), in `src/demo.cpp`:** the driver looks for a finished turn at 200 Hz instead of 10 Hz. The LD19 turns at about 9.9 Hz, so the 10 Hz loop drifted into phase with it and lost whole turns (about 0.2 s without a scan, more often with the Pi busy).
  4. The original's two udev shell scripts (`scripts/create_udev_rules.sh`, `delete_udev_rules.sh`) were removed; the car uses `tools/99-robotek.rules`.
* This driver is written in C++. It is the third-party code of the car; the code of the team is in Python.
* The `.git` directory of the original was not copied.
