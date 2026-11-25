"""
Open Challenge: bring up the sim (world + robot + bridge) and the strategy.

ros2 launch robotek_bringup open_challenge.launch.py
ros2 launch robotek_bringup open_challenge.launch.py direction:=cw gui:=false
"""
import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetLaunchConfiguration, Shutdown,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from robotek_open.open_profile import validate_parameters


def _strategy(context):
    if LaunchConfiguration('strategy').perform(context) != 'v5':
        raise RuntimeError('Only the Open v5 strategy exists (v4 and older were removed on 26 oct 2026).')
    params_file = LaunchConfiguration('params_file').perform(context)
    if params_file:
        with open(params_file) as stream:
            params = yaml.safe_load(stream)['open_strategy']['ros__parameters']
        validate_parameters(params, allowed=('use_sim_time',))
    parameters = [params_file] if params_file else []
    overrides = {}
    direction = LaunchConfiguration('direction').perform(context)
    if direction:
        overrides['direction'] = direction
    # Control timer and node clock follow /clock: the same steps per simulated
    # second whatever the real-time factor (GUI, headless or accelerated).
    overrides['use_sim_time'] = True
    parameters.append(overrides)
    return [Node(
        package='robotek_open', executable='open_strategy_v5', name='open_strategy',
        output='screen', on_exit=Shutdown(), parameters=parameters,
        remappings=_actuator_remap(context),
    )]


def _audit(context):
    # Audit-only: robot contact sensors; the world needs gz-sim-contact-system.
    directory = LaunchConfiguration('audit_dir').perform(context)
    if not directory:
        return []
    nodes = [
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=['/audit/robot_contacts@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts'],
             parameters=[{'use_sim_time': True}], output='screen'),
        Node(package='robotek_evaluation', executable='obstacle_audit_recorder',
             parameters=[{'output_dir': directory, 'use_sim_time': True}], output='screen'),
    ]
    # Ground truth for the judge only; the strategy has no pose subscriptions.
    nodes.append(Node(package='robotek_evaluation', executable='audit_pose_recorder',
                      parameters=[{'output_dir': directory, 'use_sim_time': True}],
                      output='screen'))
    return nodes


def _real_on(context):
    return LaunchConfiguration('real_car').perform(context).lower() == 'true'


def _actuator_on(context):
    return (LaunchConfiguration('actuator_model').perform(context).lower() == 'true'
            or _real_on(context))


def _actuator_remap(context):
    # With the actuator model the strategy feeds it, and it feeds the plugin.
    return [('/cmd_vel', '/cmd_vel_raw')] if _actuator_on(context) else []


def _actuator(context):
    if not _actuator_on(context):
        return []
    if _real_on(context):
        # Servo, motor and speed table measured on the real car (real_car_v1.yaml).
        real = os.path.join(get_package_share_directory('robotek_evaluation'), 'config', 'real_car_v1.yaml')
        return [Node(package='robotek_evaluation', executable='sim_actuator_model',
                     name='sim_actuator_model', output='screen',
                     parameters=[real, {'use_sim_time': True}])]
    params = {k: float(LaunchConfiguration(k).perform(context)) for k in
              ('steer_delay', 'steer_rate', 'steer_tau', 'accel_max')}
    params.update(decel_max=params['accel_max'], use_sim_time=True)
    return [Node(package='robotek_evaluation', executable='sim_actuator_model',
                 name='sim_actuator_model', output='screen', parameters=[params])]


def _real_scan(context):
    # real_car: Gazebo's LiDAR goes to /scan_gz; sim_scan_model adds the LD19 dropouts -> /scan.
    if not _real_on(context):
        return []
    return [Node(package='ros_gz_bridge', executable='parameter_bridge', name='scan_gz_bridge',
                 arguments=['/scan_gz@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'],
                 parameters=[{'use_sim_time': True}], output='screen'),
            Node(package='robotek_evaluation', executable='sim_scan_model', name='sim_scan_model',
                 parameters=[{'use_sim_time': True}], output='screen')]


def _plugin_acceleration(context):
    # The plugin's limit also caps yaw-rate changes; lift it when modelled here.
    return '30.0' if _actuator_on(context) else LaunchConfiguration('ackermann_acceleration').perform(context)


def generate_launch_description():
    sim_launch = os.path.join(
        get_package_share_directory('robotek_gazebo'), 'launch', 'robotek_sim.launch.py'
    )

    return LaunchDescription([
        DeclareLaunchArgument('direction', default_value='',
                              description='cw/ccw/auto override; otherwise YAML or auto default.'),
        DeclareLaunchArgument('strategy', default_value='v5', description='v5 (robotek_open.v5), the only Open strategy'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('world', default_value='',
                              description='Optional Open field SDF override.'),
        DeclareLaunchArgument('params_file', default_value='',
                              description='Optional strategy ROS parameter YAML file.'),
        DeclareLaunchArgument('ackermann_velocity_limit', default_value='1.0'),
        DeclareLaunchArgument('ackermann_steer_p_gain', default_value='1.0'),
        DeclareLaunchArgument('ackermann_acceleration', default_value='2.0'),
        DeclareLaunchArgument('audit_dir', default_value='',
                              description='If set, record robot contacts (walls) there.'),
        DeclareLaunchArgument('actuator_model', default_value='false',
                              description='true: model servo/motor in sim_actuator_model '
                                          '(see that node) instead of the plugin limit.'),
        DeclareLaunchArgument('real_car', default_value='true',
                              description='true (default since 9 Oct 2026): actuators (real_car_v1.yaml) '
                                          'and sensors (IMU 50 Hz, camera 6 fps, LiDAR blind behind) '
                                          'measured on the real car; implies the actuator model. '
                                          'false: the older idealised car.'),
        DeclareLaunchArgument('steer_delay', default_value='0.03'),
        DeclareLaunchArgument('steer_rate', default_value='4.4'),
        DeclareLaunchArgument('steer_tau', default_value='0.03'),
        DeclareLaunchArgument('accel_max', default_value='2.0'),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='-1.0'),
        DeclareLaunchArgument('spawn_yaw', default_value='0.0'),
        OpaqueFunction(function=lambda context: [SetLaunchConfiguration(
            'plugin_acceleration', _plugin_acceleration(context)),
            # Honest simulation only: sensor noise is always on (no honest:=false since 9 Oct 2026).
            SetLaunchConfiguration('sensor_noise_effective', 'true')]),
        OpaqueFunction(function=_actuator),
        OpaqueFunction(function=_real_scan),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                'ackermann_velocity_limit': LaunchConfiguration('ackermann_velocity_limit'),
                'ackermann_steer_p_gain': LaunchConfiguration('ackermann_steer_p_gain'),
                'ackermann_acceleration': LaunchConfiguration('plugin_acceleration'),
                'sensor_noise': LaunchConfiguration('sensor_noise_effective'),
                'real_sensors': LaunchConfiguration('real_car'),
                'field': 'open',            # Open Challenge = no obstacles
                'world': LaunchConfiguration('world'),
                'gui': LaunchConfiguration('gui'),
                'spawn_x': LaunchConfiguration('spawn_x'),
                'spawn_y': LaunchConfiguration('spawn_y'),
                'spawn_yaw': LaunchConfiguration('spawn_yaw'),
            }.items(),
        ),
        OpaqueFunction(function=_strategy),
        OpaqueFunction(function=_audit),
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             condition=IfCondition(LaunchConfiguration('rviz')),
             arguments=['-d', os.path.join(get_package_share_directory('robotek_description'), 'rviz', 'open_camera.rviz')],
             parameters=[{'use_sim_time': True}]),
    ])
