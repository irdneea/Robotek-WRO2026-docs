#!/usr/bin/env bash
set -e

# Mantiene el mismo dominio ROS usado por la configuración anterior.
export ROS_DOMAIN_ID=1

mode="$(tr -d '[:space:]' < /home/user/.config/wro_mode 2>/dev/null || echo open)"
case "$mode" in
    open) exec /bin/bash /home/user/Documents/Testv1/open/run_open.sh ;;
    obstacle)
        source /opt/ros/jazzy/setup.bash
        source /home/user/Projects/WRO-Strategies/install/setup.bash   # el repo trae driver, peripherals y LiDAR
        exec ros2 launch rrc_lite_driver wro.launch.py
        ;;
    *) echo "Modo inválido: $mode (usa open u obstacle)" >&2; exit 2 ;;
esac