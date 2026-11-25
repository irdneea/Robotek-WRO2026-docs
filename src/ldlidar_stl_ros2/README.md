# ldlidar_stl_ros2

Driver of the LDROBOT LD19 LiDAR (also LD06 and STL27L) for ROS 2. It publishes `/scan`.

It is third-party code (MIT licence, LDROBOT) with a few changes of ours: see [NOTICE-ROBOTEK.md](NOTICE-ROBOTEK.md). Original project and full manual: https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2

It is built with the rest of the workspace (`colcon build` from the root of the repository). The car starts it from `robotek_course/launch/car.launch.py`.
