#!/usr/bin/env bash
# Rename the RRC Lite driver on the Pi (decision of 10 Oct 2026, see README.md "Nombres nuevos"):
#
#   package  ros_robot_controller       -> rrc_lite_driver
#   messages ros_robot_controller_msgs  -> rrc_lite_msgs
#   executable controller_node          -> rrc_driver      (node name rrc_driver)
#   topics   /ros_robot_controller/...  -> /rrc/...
#
# Ran on the car on 9 Oct 2026 (backup ~/rename-backup-20261009T212959). Two rules of the first
# version were too broad (package_name= and get_package_share_directory('...') became rrc_driver)
# and were fixed by hand on the Pi; they are corrected below.
#
# Run ON THE PI, with the ROS stack stopped:
#   ssh user@192.168.0.10 'bash -s' < docs/robot-real-pi/rename/rename_rrc_driver.sh
# Dry run (only shows what it would touch):
#   ssh user@192.168.0.10 'DRY_RUN=1 bash -s' < docs/robot-real-pi/rename/rename_rrc_driver.sh
#
# Nothing is deleted: the old sources, scripts and install/build folders are moved to
# ~/rename-backup-<stamp>/. Rollback instructions are printed at the end.
set -euo pipefail

WS=${WS:-$HOME/wro_controller_ws}
STAMP=$(date +%Y%m%dT%H%M%S)
BACKUP=$HOME/rename-backup-$STAMP
DRY=${DRY_RUN:-0}
# Only what uses ~/wro_controller_ws. NOT touched: ~/Documents/Testv1 (team archive) and the open-mode
# stack ~/Documents/Testv1/open, which runs on its own copy ~/Documents/wro_controller_ws-copy with
# the old names (self-consistent). stop_ros.sh keeps matching both old and new process names.
EXTRA_DIRS=("$HOME/scripts")

say() { printf '\n== %s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then echo "DRY: $*"; else "$@"; fi; }

# --- 0. checks -------------------------------------------------------------------------------
if ps -eo args | grep -E '[r]os2 (launch|run)|[c]ontroller_node|[r]rc_driver' >/dev/null; then
    echo "ROS nodes are running: stop them first (~/scripts/stop_ros.sh)." >&2
    exit 1
fi
find_pkg() {  # directory of the package whose package.xml has <name>$1</name>
    grep -rl --include=package.xml "<name>$1</name>" "$WS/src" | head -1 | xargs -r dirname
}
DRV=$(find_pkg ros_robot_controller)
MSGS=$(find_pkg ros_robot_controller_msgs)
if [ -z "$DRV" ] || [ -z "$MSGS" ]; then
    echo "ros_robot_controller / ros_robot_controller_msgs not found under $WS/src (already renamed?)." >&2
    find_pkg rrc_lite_driver; find_pkg rrc_lite_msgs
    exit 1
fi
echo "driver:   $DRV"
echo "messages: $MSGS"

# --- 1. backup --------------------------------------------------------------------------------
say "Backup in $BACKUP"
run mkdir -p "$BACKUP"
run cp -a "$WS/src" "$BACKUP/src"
for d in "${EXTRA_DIRS[@]}"; do
    [ -d "$d" ] && run mkdir -p "$BACKUP/extra$(dirname "$d")" && run cp -a "$d" "$BACKUP/extra$d"
done

# --- 2. rename folders and files ---------------------------------------------------------------
say "Rename folders and files"
NEW_DRV=$(dirname "$DRV")/rrc_lite_driver
NEW_MSGS=$(dirname "$MSGS")/rrc_lite_msgs
run mv "$DRV" "$NEW_DRV"
run mv "$MSGS" "$NEW_MSGS"
[ "$DRY" = 1 ] && NEW_DRV=$DRV
mvif() { [ -e "$1" ] && run mv "$1" "$2" || true; }
mvif "$NEW_DRV/ros_robot_controller" "$NEW_DRV/rrc_lite_driver"
mvif "$NEW_DRV/resource/ros_robot_controller" "$NEW_DRV/resource/rrc_lite_driver"
PYDIR=$NEW_DRV/rrc_lite_driver; [ "$DRY" = 1 ] && PYDIR=$NEW_DRV/ros_robot_controller
mvif "$PYDIR/ros_robot_controller_sdk" "$PYDIR/rrc_lite_driver_sdk"
mvif "$PYDIR/controller_node.py" "$PYDIR/rrc_driver.py"
mvif "$NEW_DRV/launch/ros_robot_controller.launch.py" "$NEW_DRV/launch/rrc_lite_driver.launch.py"

# --- 3. replace names inside text files ---------------------------------------------------------
say "Replace names in text files"
SED=$(mktemp)
cat > "$SED" <<'EOF'
s#ros_robot_controller_msgs#rrc_lite_msgs#g
s#/ros_robot_controller/\(battery\|button\|imu_raw\|joy\|sbus\|set_\|enable_reception\|pwm_servo\|bus_servo\|acker_servo\|init_finish\|get_\)#/rrc/\1#g
s#controller_node *= *ros_robot_controller\.controller_node:main#rrc_driver = rrc_lite_driver.rrc_driver:main#g
s#ros_robot_controller\.controller_node#rrc_lite_driver.rrc_driver#g
s#executable *= *'controller_node'#executable='rrc_driver'#g
s#executable *= *"controller_node"#executable="rrc_driver"#g
s#\bname *= *\(['"]\)ros_robot_controller\(['"]\)#name=\1rrc_driver\2#g
s#RosRobotController(\(['"]\)ros_robot_controller#RosRobotController(\1rrc_driver#g
s#ros_robot_controller#rrc_lite_driver#g
s#controller_node#rrc_driver#g
EOF
TARGETS=("$WS/src")
for d in "${EXTRA_DIRS[@]}"; do [ -d "$d" ] && TARGETS+=("$d"); done
GREP_EXCL=(--exclude='*.bak*' --exclude='*.log' --exclude-dir=.git --exclude-dir=build --exclude-dir=install --exclude-dir=log)
mapfile -t FILES < <(grep -rIl -e ros_robot_controller -e controller_node "${TARGETS[@]}" "${GREP_EXCL[@]}" 2>/dev/null || true)
printf '%s\n' "${FILES[@]}"
for f in "${FILES[@]}"; do run sed -i -f "$SED" "$f"; done
STOP=$HOME/scripts/stop_ros.sh
if [ -f "$STOP" ] && [ "$DRY" != 1 ] && ! grep -q 'ros_robot_controller/\.\*/controller_node' "$STOP"; then
    sed -i "s#rrc_lite_driver/\.\*/rrc_driver'#rrc_lite_driver/.*/rrc_driver|ros_robot_controller/.*/controller_node'#" "$STOP"
    grep -n ROS_STACK_PATTERN= "$STOP"
fi

# The driver's topics were private (~/battery -> /<node name>/battery). Make them /rrc/...
DRV_PY=$PYDIR/rrc_driver.py; [ "$DRY" = 1 ] && DRV_PY=$PYDIR/controller_node.py
if [ -f "$DRV_PY" ]; then
    say "Topics of $DRV_PY: ~/x -> rrc/x"
    grep -n "[\"']~/" "$DRV_PY" || true
    run sed -i "s#\([\"']\)~/#\1rrc/#g" "$DRV_PY"
fi

# --- 4. move old build/install out of the way and rebuild ---------------------------------------
say "Old build/install folders -> backup"
for sub in build install; do
    for p in ros_robot_controller ros_robot_controller_msgs; do
        [ -e "$WS/$sub/$p" ] && run mkdir -p "$BACKUP/$sub" && run mv "$WS/$sub/$p" "$BACKUP/$sub/$p"
    done
done
say "colcon build"
if [ "$DRY" != 1 ]; then
    set +u; source /opt/ros/jazzy/setup.bash; set -u
    (cd "$WS" && colcon build 2>&1 | tail -5)
    systemctl --user daemon-reload 2>/dev/null || true
fi

# --- 5. check ------------------------------------------------------------------------------------
say "Leftover old names (should be empty)"
grep -rIn -e ros_robot_controller -e controller_node "${TARGETS[@]}" "${GREP_EXCL[@]}" 2>/dev/null \
    | grep -v 'ros_robot_controller/.\*/controller_node' | head -20 || true
if [ "$DRY" != 1 ]; then
    set +u; source "$WS/install/setup.bash"; set -u
    echo "executables:"; ros2 pkg executables rrc_lite_driver || true
fi
cat <<EOF

Done. Test: ros2 run rrc_lite_driver rrc_driver   then   ros2 topic list | grep /rrc/
Then copy our repo again from the Mac and rebuild it (it already uses the new names).

Rollback (nothing was deleted):
  mv $WS/src $WS/src-renamed-$STAMP && cp -a $BACKUP/src $WS/src
  cp -a $BACKUP/extra$HOME/scripts/. $HOME/scripts/   (same for Documents/Testv1, .config/systemd/user)
  mv $BACKUP/install/* $WS/install/ ; mv $BACKUP/build/* $WS/build/ ; cd $WS && colcon build
EOF
