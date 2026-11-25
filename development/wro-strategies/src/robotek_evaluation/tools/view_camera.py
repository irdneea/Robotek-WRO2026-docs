#!/usr/bin/env python3
"""Keep Gazebo and RViz open at the start, without continuously recording raw scans."""
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
import devenv  # noqa: E402


def main():
    import yaml
    os.chdir(devenv.ROOT)
    env = devenv.workspace_env()
    devenv.run_tool(HERE / 'clean_sim.py', env=env)
    viewer = devenv.ROOT / 'docs/open-challenge-runs/camera-live'
    viewer.mkdir(parents=True, exist_ok=True)
    parameters = yaml.safe_load((devenv.ROOT / 'src/robotek_open/config/open_v5.yaml').read_text())
    parameters['open_strategy']['ros__parameters'].update(auto_start=False, shutdown_on_done=False, telemetry_path='')
    (viewer / 'params.yaml').write_text(yaml.safe_dump(parameters))
    env['ROS_LOG_DIR'] = str(viewer / 'ros-log')
    print(f'Camera viewer: {viewer}/launch.log', flush=True)
    log = os.open(viewer / 'launch.log', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    os.dup2(log, 1)
    os.dup2(log, 2)
    os.execvpe('ros2', ['ros2', 'launch', 'robotek_bringup', 'open_challenge.launch.py', 'gui:=true', 'rviz:=true',
                        'direction:=auto', 'spawn_y:=-1.15', f'params_file:={viewer}/params.yaml'], env)


if __name__ == '__main__':
    sys.exit(main())
