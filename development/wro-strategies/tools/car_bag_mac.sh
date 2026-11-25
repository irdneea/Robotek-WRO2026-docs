#!/usr/bin/env bash
# Records the real car's run from the Mac (Wi-Fi) into a rosbag, with the RoboStack environment.
#
#   bash tools/car_bag_mac.sh [name]          # Ctrl+C to stop; ~/rondas-coche/bags/<date-time>-<name>/
#   CAMERA=1 bash tools/car_bag_mac.sh        # also the strategy's debug image (heavier over Wi-Fi)
#
# Topics: the LiDAR (raw and adapted), IMU, rear distance sensor, the GPIO button and Start, the commands
# (/cmd_vel_raw, motor, servo, estop), the strategy's state, pose and signs, battery, /tf_static and /rosout
# (the strategy's log lines, the lot exit's included).
# Network as tools/macos_rviz_real.sh (Cyclone DDS, domain 1, discovery on the subnet): the Pi must run the
# same (car-autostart.sh does; a manual launch needs RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET). The bags are telemetry: they stay on this Mac, not in git.
cd "$(dirname "$0")/.." || exit 1
NAME=${1:-car}
set --   # macos_env.sh takes $1 as the RoboStack environment path
source tools/macos_env.sh >/dev/null 2>&1 || exit 1
PI_IP=${PI_IP:-192.168.0.10}
export RMW_IMPLEMENTATION=${REAL_CAR_RMW:-rmw_cyclonedds_cpp}
export ROS_DOMAIN_ID=${REAL_CAR_DOMAIN_ID:-1} ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_STATIC_PEERS=${ROS_STATIC_PEERS:-$PI_IP}
if [ "$RMW_IMPLEMENTATION" = rmw_cyclonedds_cpp ]; then
  IFACE=$(route -n get "$PI_IP" 2>/dev/null | awk '/interface:/{print $2}')
  [ -n "$IFACE" ] && export CYCLONEDDS_URI="<CycloneDDS><Domain><General><Interfaces><NetworkInterface name=\"$IFACE\" multicast=\"true\"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>"
fi
OUT="$HOME/rondas-coche/bags/$(date +%Y%m%d-%H%M%S)-$NAME"
mkdir -p "$(dirname "$OUT")"
TOPICS=(/scan /robotek/scan /robotek/imu /rrc/imu_raw /robotek/rear_range_mm /robotek/rear_range
        /robotek/gpio_button /start /robotek/stop /robotek/estop /cmd_vel_raw /rrc/set_motor
        /rrc/acker_servo/set_state /robotek/state /obstacle/pose /obstacle/signs /rrc/battery
        /tf_static /rosout)
[ "${CAMERA:-0}" = 1 ] && TOPICS+=(/obstacle/debug_image/compressed)
echo "bag: $OUT (RMW=$RMW_IMPLEMENTATION domain=$ROS_DOMAIN_ID Pi=$PI_IP ${IFACE:+interface=$IFACE})"
ros2 daemon stop >/dev/null 2>&1   # the daemon keeps the previous RMW/domain
exec ros2 bag record -o "$OUT" "${TOPICS[@]}"
