"""
Real car: hardware adapters + one strategy, same code as in simulation.

  ros2 launch robotek_bringup robot.launch.py challenge:=open
  ros2 launch robotek_bringup robot.launch.py challenge:=obstacle            (v3: laps, then parks)
  ros2 launch robotek_bringup robot.launch.py challenge:=obstacle mode:=laps  (v3: laps only, no lot)
  ros2 launch robotek_bringup robot.launch.py challenge:=obstacle mode:=park  (v3: parks right away)
  ros2 launch robotek_bringup robot.launch.py challenge:=obstacle strategy:=v1 (the original node)
  ros2 launch robotek_bringup robot.launch.py challenge:=open controller:=false lidar_package:= camera:=false
      (board, lidar and camera already running, e.g. from peripherals sensors.launch.py)

Starts (each optional part is skipped with a warning when its package is missing, so
the launch can be dry-run on a PC):
  - HiWonder RRC Lite driver (rrc_lite_driver controller.launch.py): IMU, button, servo, buzzer
  - lidar driver (peripherals lidar.launch.py: the LD19), 5 s after the board (started together
    the lidar times out); lidar_package:= (empty) when it runs separately
    + scan_adapter: <raw_scan_topic> -> /robotek/scan (0 rad ahead)
  - camera, 7 s after the board: peripherals camera_publisher (also publishes .../compressed for
    RViz), or usb_cam when peripherals is missing -> <camera_topic>
  - robotek_hardware: motor_driver (TB6612, with reverse), base_adapter (/cmd_vel ->
    servo us + motor %), start_button (button -> /start; pressed again -> /robotek/stop)
  - battery_guard (on by default): below battery_min_v (6.8 V) it only warns (status_leds blinks
    red): change the battery before the next round; it never stops the car
  - status_leds (on by default): the two board RGBs show ready / missing sensor / calibrating /
    done / low battery (the buzzer is burnt out); status_leds:=false turns it off
  - robot_state_publisher with robotek_description (TF for RViz on a PC)
  - the strategy: use_sim_time false, auto_start false (waits for the button),
    telemetry in <run_dir>/<UTC stamp>-<challenge>/
No ground truth, judge or actuator model here: those are simulation-only (robotek_evaluation).
"""
import datetime
import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# Seconds after the board driver (as peripherals sensors.launch.py): the LD19 started together with the
# board times out, and the camera shares the USB2 bus with the lidar.
LIDAR_DELAY, CAMERA_DELAY = 5.0, 7.0
REAL_OBSTACLE_STEER_LIMIT = 0.3054   # rad = 17.5 deg: the Obstacle on the real car since 8 nov 2026

# Real field (8 oct 2026, docs/robot-real.md): the "orange" line looks red (H 163-178) and
# the blue one is darker than in Gazebo; the beige room wall above the black field wall is
# in the simulation's orange range, so only the floor below the wall is used.
REAL_OPEN_CAMERA = {
    'vision_blue_h_min': 100, 'vision_blue_h_max': 135, 'vision_blue_s_min': 80, 'vision_blue_v_min': 25,
    'vision_orange_h_min': 158, 'vision_orange_h_max': 4, 'vision_orange_s_min': 60, 'vision_orange_v_min': 40,
    'vision_floor_mask': True,
}

# (challenge, strategy) -> (package, executable, profile); the first strategy of each challenge is the default.
PROFILES = {
    ('open', 'v5'): ('robotek_open', 'open_strategy_v5', 'open_v5.yaml'),   # not tried on the real car yet
    ('obstacle', 'v3'): ('robotek_obstacle', 'obstacle_strategy_v3', 'obstacle_v3.yaml'),   # not tried on the real car yet
    ('obstacle', 'v2'): ('robotek_obstacle', 'obstacle_strategy_v2', 'obstacle_v2.yaml'),
    ('obstacle', 'v1'): ('robotek_obstacle', 'obstacle_strategy', 'obstacle_sensors_v1.yaml'),
}
DEFAULT_STRATEGY = {'open': 'v5', 'obstacle': 'v3'}
# v2/v3 take park/park_after instead of the original node's mode (laps | park).
V2_MODES = {'': {'park': 1.0}, 'laps': {'park': 0.0}, 'park': {'park': 1.0, 'park_after': 0.0}}


def _share(package):
    try:
        return get_package_share_directory(package)
    except PackageNotFoundError:
        return None


def _arg(context, name):
    return LaunchConfiguration(name).perform(context)


def _drivers(context):
    actions = []
    if _arg(context, 'controller').lower() == 'true':
        share = _share('rrc_lite_driver')
        launch = os.path.join(share or '', 'launch', _arg(context, 'controller_launch'))
        if share and os.path.exists(launch):
            actions.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(launch)))
        else:
            actions.append(LogInfo(msg='[robot] rrc_lite_driver launch not found: start the RRC Lite '
                                       'driver separately (IMU, button, servo).'))
    package, launch_file = _arg(context, 'lidar_package'), _arg(context, 'lidar_launch')
    if package and launch_file:
        share = _share(package)
        if share:
            actions.append(TimerAction(period=LIDAR_DELAY, actions=[IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(share, 'launch', launch_file)))]))
        else:
            actions.append(LogInfo(msg=f'[robot] lidar package {package} not found.'))
    else:
        actions.append(LogInfo(msg='[robot] lidar driver not launched here: it must publish '
                                   + _arg(context, 'raw_scan_topic')))
    if _arg(context, 'camera').lower() == 'true':
        if _share('peripherals'):
            actions.append(TimerAction(period=CAMERA_DELAY, actions=[Node(
                package='peripherals', executable='camera_publisher', name='usb_cam', output='screen',
                parameters=[{'device': _arg(context, 'video_device')}])]))
        elif _share('usb_cam'):
            actions.append(Node(package='usb_cam', executable='usb_cam_node_exe', name='usb_cam',
                                namespace='usb_cam', output='screen',
                                parameters=[{'video_device': _arg(context, 'video_device'),
                                             'image_width': 640, 'image_height': 480,
                                             'framerate': 30.0, 'pixel_format': 'yuyv'}]))
        else:
            actions.append(LogInfo(msg='[robot] usb_cam not found: the camera must publish '
                                       + _arg(context, 'camera_topic')))
    return actions


def _strategy(context):
    challenge = _arg(context, 'challenge')
    if challenge not in DEFAULT_STRATEGY:
        raise RuntimeError('challenge must be open or obstacle')
    strategy = _arg(context, 'strategy') or DEFAULT_STRATEGY[challenge]
    if (challenge, strategy) not in PROFILES:
        raise RuntimeError(f'{challenge} has no strategy {strategy}: '
                           + ', '.join(s for c, s in PROFILES if c == challenge)
                           + (' (Open v4 and older were removed on 26 oct 2026)' if challenge == 'open' else ''))
    package, executable, profile = PROFILES[challenge, strategy]
    profile = _arg(context, 'profile') or os.path.join(get_package_share_directory(package), 'config', profile)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_dir = os.path.join(os.path.expanduser(_arg(context, 'run_dir')), f'{stamp}-{challenge}')
    sim_time = _arg(context, 'use_sim_time').lower() == 'true'
    overrides = {'use_sim_time': sim_time, 'auto_start': False,
                 'telemetry_path': os.path.join(run_dir, 'telemetry.csv')}
    if challenge == 'open':
        overrides['shutdown_on_done'] = False   # keep the car stopped, do not tear the launch down
        overrides.update(REAL_OPEN_CAMERA)
        overrides['telemetry_sync_seconds'] = 0.5  # a power cut lost a whole run (8 oct 2026)
    mode = _arg(context, 'mode')
    if challenge == 'obstacle' and strategy == 'v1' and mode:
        overrides['mode'] = mode
    if challenge == 'obstacle' and strategy != 'v1':
        if mode not in V2_MODES:
            raise RuntimeError("mode must be '', laps or park")
        overrides.update(V2_MODES[mode])
    if challenge == 'obstacle':
        # 17.5 deg on the car (user, 8 nov 2026): the setting of the best car round (DONE 85.0 s, robotek-learn
        # car.launch default). REAL_STEER_LIMIT (17.6) stays the lab's and Gazebo's.
        overrides['steer_limit'] = REAL_OBSTACLE_STEER_LIMIT   # base_adapter makes it the same on both sides
        from robotek_common.vehicle import REAL_CAMERA_HFOV, REAL_CAMERA_PITCH, REAL_CAMERA_YAW
        overrides.update(camera_hfov=REAL_CAMERA_HFOV, camera_pitch=REAL_CAMERA_PITCH,
                         camera_yaw=REAL_CAMERA_YAW)
    remappings = [('/scan', '/robotek/scan'), ('scan', '/robotek/scan'),
                  ('/imu', '/robotek/imu'), ('imu', '/robotek/imu'),   # imu_adapter: car frame
                  ('/camera/image', _arg(context, 'camera_topic'))]
    # The obstacle profiles are all written for the node name obstacle_strategy (as in simulation).
    name = 'obstacle_strategy' if challenge == 'obstacle' else executable
    return [LogInfo(msg=f'[robot] {challenge} {strategy}: profile {profile}, telemetry in {run_dir}'),
            Node(package=package, executable=executable, name=name, output='screen',
                 parameters=[profile, overrides], remappings=remappings)]


def generate_launch_description():
    hardware_config = os.path.join(get_package_share_directory('robotek_hardware'), 'config', 'robot.yaml')
    urdf = os.path.join(get_package_share_directory('robotek_description'), 'urdf', 'robotek.urdf.xacro')
    return LaunchDescription([
        DeclareLaunchArgument('challenge', default_value='open', description='open or obstacle'),
        DeclareLaunchArgument('strategy', default_value='',
                              description='open: v5 (the only one); obstacle: v3 (default), v2 or v1 (the original node)'),
        DeclareLaunchArgument('profile', default_value='', description='strategy YAML (default: the active profile)'),
        DeclareLaunchArgument('mode', default_value='',
                              description="obstacle only: '' (v3/v2: laps, then park), 'laps' or 'park' (only park)"),
        DeclareLaunchArgument('run_dir', default_value='~/robotek-runs'),
        DeclareLaunchArgument('controller', default_value='true'),
        DeclareLaunchArgument('controller_launch', default_value='controller.launch.py'),
        DeclareLaunchArgument('lidar_package', default_value='peripherals'),
        DeclareLaunchArgument('lidar_launch', default_value='lidar.launch.py'),
        DeclareLaunchArgument('raw_scan_topic', default_value='/scan'),
        DeclareLaunchArgument('imu_topic', default_value='/rrc/imu_raw'),
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='true only to test this launch against Gazebo on a PC'),
        DeclareLaunchArgument('battery_guard', default_value='true',
                              description='red blinking RGBs when the battery is low (does not stop the car)'),
        DeclareLaunchArgument('battery_min_v', default_value='6.8',
                              description='battery voltage (V) under which to change the battery'),
        DeclareLaunchArgument('gpio_button', default_value='true',
                              description='push button on a Pi GPIO -> /robotek/gpio_button (Bool, true = pressed); '
                                          'only reports for now, it does not start or stop the round'),
        DeclareLaunchArgument('gpio_button_pin', default_value='16',
                              description='BCM GPIO of the push button (other leg on GND, internal pull-up)'),
        DeclareLaunchArgument('rear_range', default_value='true',
                              description='VL53L0X distance sensor on the Pi I2C bus -> /robotek/rear_range (Range, m) '
                                          'and /robotek/rear_range_mm (Int32, mm); only reports for now'),
        DeclareLaunchArgument('status_leds', default_value='true',
                              description='state on the RRC Lite RGBs (green = ready for Start)'),
        DeclareLaunchArgument('camera', default_value='true'),
        DeclareLaunchArgument('video_device', default_value='/dev/v4l/by-id/usb-icSpring_icspring_camera-video-index0',
                              description='camera by USB id (not /dev/videoN, whose number can change)'),
        DeclareLaunchArgument('camera_topic', default_value='/usb_cam/image_raw'),
        OpaqueFunction(function=_drivers),
        Node(package='robotek_hardware', executable='scan_adapter', name='scan_adapter', output='screen',
             parameters=[hardware_config],
             remappings=[('scan_in', LaunchConfiguration('raw_scan_topic')), ('scan_out', '/robotek/scan')]),
        Node(package='robotek_hardware', executable='imu_adapter', name='imu_adapter', output='screen',
             parameters=[hardware_config],
             remappings=[('imu_in', LaunchConfiguration('imu_topic')), ('imu_out', '/robotek/imu')]),
        Node(package='robotek_hardware', executable='motor_driver', name='tb6612fng_motor', output='screen',
             parameters=[hardware_config]),
        Node(package='robotek_hardware', executable='base_adapter', name='base_adapter', output='screen',
             parameters=[hardware_config], remappings=[('cmd_vel', '/cmd_vel')]),
        Node(package='robotek_hardware', executable='start_button', name='start_button', output='screen',
             remappings=[('start', '/start')]),
        Node(package='robotek_hardware', executable='gpio_button', name='gpio_button', output='screen',
             condition=IfCondition(LaunchConfiguration('gpio_button')),
             parameters=[{'pin': ParameterValue(LaunchConfiguration('gpio_button_pin'), value_type=int)}]),
        Node(package='robotek_hardware', executable='rear_range', name='rear_range', output='screen',
             condition=IfCondition(LaunchConfiguration('rear_range'))),
        Node(package='robotek_hardware', executable='battery_guard', name='battery_guard', output='screen',
             condition=IfCondition(LaunchConfiguration('battery_guard')),
             parameters=[{'min_voltage': ParameterValue(LaunchConfiguration('battery_min_v'), value_type=float)}]),
        Node(package='robotek_hardware', executable='status_leds', name='status_leds', output='screen',
             condition=IfCondition(LaunchConfiguration('status_leds')),
             parameters=[{'imu_topic': LaunchConfiguration('imu_topic'),
                          'camera_topic': LaunchConfiguration('camera_topic'),
                          'camera_required': ParameterValue(LaunchConfiguration('camera'), value_type=bool)}]),
        Node(package='robot_state_publisher', executable='robot_state_publisher', output='screen',
             parameters=[{'robot_description': ParameterValue(Command(['xacro ', urdf]), value_type=str)}]),
        OpaqueFunction(function=_strategy),
    ])
