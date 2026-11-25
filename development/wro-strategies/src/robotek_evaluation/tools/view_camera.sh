#!/usr/bin/env bash
# Keep Gazebo and RViz open at the start, without continuously recording raw scans.
set -eo pipefail
cd "$(dirname "$0")/../../.."
# Linux: system ROS. macOS (RoboStack): source tools/macos_env.sh first (docs/simulacion-macos.md).
if [ -f /opt/ros/jazzy/setup.bash ]; then source /opt/ros/jazzy/setup.bash; fi
source install/setup.bash
bash src/robotek_evaluation/tools/clean_sim.sh
viewer_dir="$PWD/docs/open-challenge-runs/camera-live"
mkdir -p "$viewer_dir"
python3 - <<'PY'
from pathlib import Path
import yaml

root = Path.cwd()
parameters = yaml.safe_load((root / 'src/robotek_open/config/open_v5.yaml')
                            .read_text())
parameters['open_strategy']['ros__parameters'].update(
    auto_start=False, shutdown_on_done=False, telemetry_path='')
(root / 'docs/open-challenge-runs/camera-live/params.yaml').write_text(
    yaml.safe_dump(parameters))
PY
export ROS_LOG_DIR="$viewer_dir/ros-log"
echo "Camera viewer: $viewer_dir/launch.log"
exec ros2 launch robotek_bringup open_challenge.launch.py \
  gui:=true rviz:=true direction:=auto spawn_y:=-1.15 \
  params_file:="$viewer_dir/params.yaml" > "$viewer_dir/launch.log" 2>&1
