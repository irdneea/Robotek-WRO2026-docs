#!/usr/bin/env bash
# En el Pi: usar Cyclone DDS, dominio 1 y descubrimiento en la subred por defecto (igual que el Mac).
# Primero, a mano y con sudo (el Pi no lo trae):
#   sudo apt install ros-jazzy-rmw-cyclonedds-cpp
# Después, desde el Mac:   ssh user@192.168.0.10 'bash -s' < tools/pi_use_cyclone.sh
# o en el propio Pi:        bash tools/pi_use_cyclone.sh
# No cambia nada si Cyclone no está instalado (un RMW que no existe rompe todos los comandos ROS).
# Es idempotente: añade un bloque marcado a ~/.bashrc una sola vez. Los nodos que ya corren siguen con
# el RMW con el que arrancaron: hay que relanzarlos para que usen Cyclone.
set -eu
if [ ! -e /opt/ros/jazzy/lib/librmw_cyclonedds_cpp.so ]; then
  echo "Cyclone DDS no está instalado: ejecuta primero  sudo apt install ros-jazzy-rmw-cyclonedds-cpp" >&2
  exit 1
fi
if grep -q "# >>> robotek dds >>>" ~/.bashrc; then
  echo "~/.bashrc ya tiene el bloque de DDS; no se cambia."
else
  cat >> ~/.bashrc <<'BLOCK'

# >>> robotek dds >>>
# Mismo RMW, dominio y descubrimiento que el Mac (README: «Red entre el Mac y el Pi»)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=1
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
# <<< robotek dds <<<
BLOCK
  echo "Añadido a ~/.bashrc: Cyclone DDS, ROS_DOMAIN_ID=1, descubrimiento SUBNET."
fi
echo "Comprobar en una terminal NUEVA:  ros2 doctor --report | grep -i 'middleware name'"
