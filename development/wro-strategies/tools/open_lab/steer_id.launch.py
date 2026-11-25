import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
def generate_launch_description():
    sim = os.path.join(get_package_share_directory('robotek_gazebo'), 'launch', 'robotek_sim.launch.py')
    real = os.path.join(get_package_share_directory('robotek_evaluation'), 'config', 'real_car_v1.yaml')
    return LaunchDescription([
        Node(package='robotek_evaluation', executable='sim_actuator_model', name='sim_actuator_model', output='log',
             parameters=[real, {'use_sim_time': True}]),
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='scan_gz_bridge',
             arguments=['/scan_gz@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'], parameters=[{'use_sim_time': True}], output='log'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim), launch_arguments={
            'ackermann_velocity_limit': '4.0', 'ackermann_steer_p_gain': '20.0', 'ackermann_acceleration': '30.0',
            'sensor_noise': 'true', 'real_sensors': 'true', 'field': 'open', 'world': '/tmp/v5/id/empty.sdf',
            'gui': 'false', 'spawn_x': '0.0', 'spawn_y': '0.0', 'spawn_yaw': '0.0'}.items()),
        Node(package='robotek_evaluation', executable='audit_pose_recorder', output='log',
             parameters=[{'output_dir': '/tmp/v5/id/out', 'use_sim_time': True}]),
    ])
