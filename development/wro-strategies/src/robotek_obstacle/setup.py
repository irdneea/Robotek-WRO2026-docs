from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'robotek_obstacle'

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
    description='Obstacle Challenge strategy for the Robotek WRO 2026 car (map-based planner): LiDAR, gyro and camera only.',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'obstacle_strategy = robotek_obstacle.obstacle_strategy_node:main',
            'obstacle_strategy_v2 = robotek_obstacle.v2.node:main',
            'obstacle_strategy_v3 = robotek_obstacle.v3.node:main',
            'obstacle_detector = robotek_obstacle.obstacle_detector_node:main',
        ],
    },
)
