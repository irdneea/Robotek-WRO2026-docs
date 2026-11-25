#!/usr/bin/env bash
# Detiene por completo el stack ROS 2 del vehículo.
set -u

# El servicio contiene el launch y todos sus nodos hijos. Al detenerlo,
# systemd envía SIGTERM al grupo completo para que motor y servo se apaguen
# mediante el cierre seguro del controlador.
systemctl --user stop ros_autostart.service 2>/dev/null || true

# Cierra procesos ROS que pudieran haberse iniciado manualmente fuera del
# servicio. Los patrones están limitados al stack del vehículo.
ROS_STACK_PATTERN='ros2 (launch|run)|ros2-daemon|local_launch[.]py|open_controller[.]py|tb6612fng_driver[.]py|ldlidar_stl_ros2_node|rrc_lite_driver/.*/rrc_driver'
pkill -TERM -u "$USER" -f "$ROS_STACK_PATTERN" 2>/dev/null || true
sleep 1
pkill -KILL -u "$USER" -f "$ROS_STACK_PATTERN" 2>/dev/null || true

echo "Stack ROS 2 del vehículo detenido."
