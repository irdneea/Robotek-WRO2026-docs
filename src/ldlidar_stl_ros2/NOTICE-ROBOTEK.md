# Provenance of this copy

This folder is a copy of the driver of the LDROBOT LD19 LiDAR (and LD06 / STL27L), included here so that `git clone` plus `colcon build` is enough on the Raspberry Pi.

* Origin: https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2, commit `bf668a89baf722a787dadc442860dcbf33a82f5a` (8 May 2023, "Update README.md").
* Licence: MIT, Copyright (c) 2020 SHENZHEN LDROBOT CO., LTD. The `LICENSE` file and the copyright notices of every file are untouched.
* Changes with respect to the original: only the two build fixes for Ubuntu 24.04 / ROS 2 Jazzy of `../robotek_hardware/patches/ldlidar_stl_ros2-build.patch`, already applied (`find_package(Threads)` and `Threads::Threads` in `CMakeLists.txt`; `#include <pthread.h>` in `ldlidar_driver/src/logger/log_module.cpp`), and a third change: on systems that are not Linux (macOS, simulation only) the `CMakeLists.txt` builds nothing, so that `colcon build` does not fail there. Nothing else was removed or added.
* The `.git` directory of the original was not copied.
