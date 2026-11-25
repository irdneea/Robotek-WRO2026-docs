#!/usr/bin/env bash
# RViz en el Mac para ver el coche real (Pi) por Wi‑Fi, con el entorno RoboStack.
#
#   bash tools/macos_rviz_real.sh                                        # robot_sensors.rviz
#   bash tools/macos_rviz_real.sh docs/robot-real-pi/robot_camera.rviz   # solo la cámara (compressed)
#
# Valores por defecto de la red Mac <-> Pi (README, «Red entre el Mac y el Pi»): Cyclone DDS, dominio 1
# y descubrimiento en la subred, iguales en los dos lados. macos_env.sh deja el Mac en dominio 42 y
# descubrimiento LOCALHOST (para la simulación): con eso el Mac no ve ningún nodo del Pi.
# Si el Pi todavía no tiene Cyclone: REAL_CAR_RMW=rmw_fastrtps_cpp bash tools/macos_rviz_real.sh
# (y el Pi con Fast DDS, que es lo que trae). Cyclone y Fast DDS NO se vieron entre sí en la prueba
# del 9 oct 2026. Cierra los RViz anteriores.
cd "$(dirname "$0")/.." || exit 1
CONFIG=${1:-docs/robot-real-pi/robot_obstacle.rviz}
set --   # macos_env.sh toma $1 como la ruta del entorno RoboStack
source tools/macos_env.sh >/dev/null 2>&1 || exit 1
PI_IP=${PI_IP:-192.168.0.10}
export RMW_IMPLEMENTATION=${REAL_CAR_RMW:-rmw_cyclonedds_cpp}
export ROS_DOMAIN_ID=${REAL_CAR_DOMAIN_ID:-1} ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_STATIC_PEERS=${ROS_STATIC_PEERS:-$PI_IP}   # descubrimiento unicast además del multicast
if [ "$RMW_IMPLEMENTATION" = rmw_cyclonedds_cpp ]; then
  IFACE=$(route -n get "$PI_IP" 2>/dev/null | awk '/interface:/{print $2}')
  [ -n "$IFACE" ] && export CYCLONEDDS_URI="<CycloneDDS><Domain><General><Interfaces><NetworkInterface name=\"$IFACE\" multicast=\"true\"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>"
fi
echo "RViz: RMW=$RMW_IMPLEMENTATION dominio=$ROS_DOMAIN_ID descubrimiento=$ROS_AUTOMATIC_DISCOVERY_RANGE Pi=$PI_IP ${IFACE:+interfaz=$IFACE}"
ros2 daemon stop >/dev/null 2>&1   # el demonio de ROS guarda el RMW/dominio anteriores
pkill -x rviz2 2>/dev/null; sleep 1
exec rviz2 -d "$CONFIG"
