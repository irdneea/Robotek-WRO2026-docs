from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'robotek_hardware'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='coach',
    maintainer_email='user@example.com',
    description='Real-car adapters (servo, motor, lidar, start button).',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'base_adapter = robotek_hardware.base_adapter:main',
            'scan_adapter = robotek_hardware.scan_adapter:main',
            'imu_adapter = robotek_hardware.imu_adapter:main',
            'imu_axes = robotek_hardware.imu_axes:main',
            'start_button = robotek_hardware.start_button:main',
            'gpio_button = robotek_hardware.gpio_button:main',
            'rear_range = robotek_hardware.rear_range:main',
            'motor_driver = robotek_hardware.motor_driver:main',
            'servo_steer = robotek_hardware.servo_steer:main',
            'actuator_test = robotek_hardware.actuator_test:main',
            'actuator_report = robotek_hardware.actuator_analysis:main',
            'power_monitor = robotek_hardware.power_monitor:main',
            'battery_guard = robotek_hardware.battery_guard:main',
            'rrc_test = robotek_hardware.rrc_test:main',
            'status_leds = robotek_hardware.status_leds:main',
        ],
    },
)
