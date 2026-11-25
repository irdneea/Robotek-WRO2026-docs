"""
Servo and motor response test on the real car (robotek_hardware/actuator_test).

  ~/scripts/stop_ros.sh                                   # the team's stack must be stopped
  source ~/wro_controller_ws/install/setup.bash && source install/setup.bash
  ros2 launch robotek_bringup actuator_test.launch.py test:=servo      # car still
  ros2 launch robotek_bringup actuator_test.launch.py test:=motor      # drives straight
  ros2 launch robotek_bringup actuator_test.launch.py test:=steer      # drives and turns

Press the board button to start; the launch ends by itself. Results in
~/robotek-runs/<UTC>-actuator-<test>/summary.json (see actuator_analysis.py).

Starts the team's drivers by executable (the RRC Lite rrc_driver for IMU, button and
servo; the LD19 through peripherals/lidar.launch.py), scan_adapter (0 rad ahead) and the
motor node: motor:=robotek (default; robotek_hardware motor_driver: drives STBY, PWM,
reverse, watchdog) or motor:=team (rrc_lite_driver motor: never sets STBY = GPIO13,
so it only moves the car when something else left that pin high; found 8 oct 2026).
Plan: steer_angles:="[10.0, 25.0]" motor_pcts:="[15.0, 20.0, 30.0]" motor_time:=0.25
steer_pct:=30.0 (decimals required). The motor runs at most 0.25 s per pulse unless
max_motor_time is raised (up to 1 s, only with every motor % <= 30); steering is clamped
to +-25 deg, whatever the arguments.
"""
import math
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription,
                            RegisterEventHandler, TimerAction)
from launch.conditions import LaunchConfigurationEquals
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


PLAN_ARGS = {
    'test': ('servo', 'servo, motor, steer or all'),
    'wait_button': ('true', 'false: start right away (no button)'),
    'steer_angles': ('[10.0, 25.0]', 'servo steps in degrees (each one +-)'),
    'motor_pcts': ('[15.0, 20.0, 30.0]', 'motor steps in %'),
    'motor_time': ('0.25', 's per motor pulse'),
    'max_motor_time': ('0.25', 'longest pulse allowed: 0.25 s, up to 1 s only at <= 30 %'),
    'steer_pct': ('30.0', 'motor % of the 0.25 s pulse of each turn'),
    'cmd_speeds': ('[0.15, 0.3]', 'test:=cmdvel speeds in m/s (at most 0.3)'),
    'circle_sides': ('both', 'test:=circle: left, right or both'),
    'circle_angles': ('[25.0, 10.0]', 'test:=circle: wheel angles in degrees'),
    'circle_pulses': ('4', 'test:=circle: motor pulses per angle'),
}


def generate_launch_description():
    hardware_config = os.path.join(get_package_share_directory('robotek_hardware'), 'config', 'robot.yaml')
    controller_params = os.path.join(get_package_share_directory('rrc_lite_driver'),
                                     'config', 'controller_params.yaml')
    lidar = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory('peripherals'), 'launch', 'lidar.launch.py')))
    test = Node(package='robotek_hardware', executable='actuator_test', name='actuator_test',
                output='screen',
                parameters=[{name: LaunchConfiguration(name) for name in PLAN_ARGS}],
                remappings=[('/imu', '/rrc/imu_raw'), ('/scan', '/robotek/scan')])
    return LaunchDescription([
        *[DeclareLaunchArgument(name, default_value=default, description=text)
          for name, (default, text) in PLAN_ARGS.items()],
        DeclareLaunchArgument('motor', default_value='robotek', description='robotek or team'),
        Node(package='rrc_lite_driver', executable='rrc_driver', name='rrc_driver',
             output='screen', parameters=[controller_params]),
        Node(package='rrc_lite_driver', executable='motor', name='motor_node', output='screen',
             condition=LaunchConfigurationEquals('motor', 'team')),
        Node(package='robotek_hardware', executable='motor_driver', name='tb6612fng_motor', output='screen',
             parameters=[hardware_config], condition=LaunchConfigurationEquals('motor', 'robotek')),
        # test:=cmdvel drives through /cmd_vel like a strategy (calibration and accel limits).
        Node(package='robotek_hardware', executable='base_adapter', name='base_adapter', output='screen',
             parameters=[hardware_config], remappings=[('cmd_vel', '/cmd_vel')],
             condition=LaunchConfigurationEquals('test', 'cmdvel')),
        TimerAction(period=5.0, actions=[lidar]),
        Node(package='robotek_hardware', executable='scan_adapter', name='scan_adapter', output='screen',
             parameters=[{'angle_offset': math.pi, 'reverse': False, 'frame_id': 'lidar_link'}],
             remappings=[('scan_in', '/scan'), ('scan_out', '/robotek/scan')]),
        TimerAction(period=8.0, actions=[test]),
        RegisterEventHandler(OnProcessExit(target_action=test, on_exit=[EmitEvent(event=Shutdown())])),
    ])
