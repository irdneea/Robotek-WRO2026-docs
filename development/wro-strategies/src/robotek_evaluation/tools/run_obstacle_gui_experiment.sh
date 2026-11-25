#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../../.."
# Linux: system ROS. macOS (RoboStack): source tools/macos_env.sh first (docs/simulacion-macos.md).
if [ -f /opt/ros/jazzy/setup.bash ]; then source /opt/ros/jazzy/setup.bash; fi
source install/setup.bash
bash src/robotek_evaluation/tools/clean_sim.sh
trap 'bash src/robotek_evaluation/tools/clean_sim.sh' EXIT
python3 src/robotek_evaluation/tools/run_obstacle_gui_experiment.py "$@"
