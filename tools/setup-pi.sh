#!/usr/bin/env bash
# Prepares a Raspberry Pi (Ubuntu 24.04, arm64) to run the strategies on the Robotek car.
#
#   git clone https://github.com/ilovmangos/Robotek-WRO2026.git && cd Robotek-WRO2026
#   bash tools/setup-pi.sh              # installs and builds (asks for sudo when needed)
#   bash tools/setup-pi.sh --check      # only checks: installs nothing and moves nothing
#   bash tools/setup-pi.sh --dry-run    # shows the commands without running them
#   bash tools/setup-pi.sh --skip-build # everything except the colcon build
#
# What it does (it can be repeated: what is already done is skipped):
#   1. checks the system (Ubuntu 24.04);
#   2. installs ROS 2 Jazzy base, without Gazebo or RViz (tools/install-ubuntu.sh --no-gazebo), and the apt packages
#      the car needs;
#   3. installs the udev rules (tools/99-robotek.rules) and adds you to the groups dialout, video and gpio;
#   4. builds the workspace: colcon build --symlink-install.
#
# SAFETY: this script starts no node and moves neither the motor nor the servo. The first time you launch the car,
# put it on supports with the wheels in the air. See src/robotek_hardware/README.md.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
DRY=0; CHECK=0; SKIP_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --check) CHECK=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg (use --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1;34m>>>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!!\033[0m %s\n' "$*" >&2; }
good() { printf '  \033[1;32mok\033[0m   %s\n' "$*"; }
bad()  { printf '  \033[1;31mFAIL\033[0m %s\n' "$*"; FAILED=1; }
note() { printf '  \033[1;33minfo\033[0m %s\n' "$*"; }
FAILED=0

# Runs a command, or only prints it with --dry-run.
run() {
  if [ "$DRY" = 1 ]; then printf '    $ %s\n' "$*"; else "$@"; fi
}

first_existing() { for f in "$@"; do [ -e "$f" ] && { echo "$f"; return 0; }; done; return 1; }

check_only() {
  say "Check (nothing is installed or moved)"
  if [ -f /opt/ros/jazzy/setup.bash ]; then good "ROS 2 Jazzy"; else bad "ROS 2 Jazzy is not installed"; fi
  if [ -d "$REPO/install" ]; then good "workspace built (install/)"; else bad "the workspace is not built: colcon build --symlink-install"; fi
  if board="$(first_existing /dev/rrc_lite /dev/ttyACM0)"; then good "RRC Lite board on $board"
  else bad "RRC Lite board (USB 1a86:55d4, /dev/ttyACM0): plug it in with the data USB cable"; fi
  if lidar="$(first_existing /dev/ldlidar /dev/ttyUSB0)"; then good "LiDAR on $lidar"
  else bad "LD19 LiDAR (USB 10c4:ea60, /dev/ttyUSB0) not found"; fi
  if command -v rpicam-vid >/dev/null 2>&1; then good "rpicam-vid (Pi camera on the flex cable, camera_driver:=picam)"
  elif camera="$(first_existing /dev/v4l/by-id/*-video-index0 2>/dev/null)"; then good "USB camera on $camera"
  else note "no rpicam-vid and no USB camera: the Open takes the direction_fallback and the LiDAR corrects it"; fi
  for group in dialout video gpio; do
    if id -nG 2>/dev/null | tr ' ' '\n' | grep -qx "$group"; then good "you are in the group $group"
    else bad "you are not in the group $group (sudo usermod -aG $group \$USER, then log in again)"; fi
  done
  [ "$FAILED" = 0 ] && say "Everything looks ready." || { warn "Something is missing (see above)."; return 1; }
}

if [ "$CHECK" = 1 ]; then check_only; exit $?; fi

# 1. System
. /etc/os-release 2>/dev/null || true
if [ "${ID:-}" != ubuntu ] || [ "${VERSION_ID:-}" != "24.04" ]; then
  warn "System ${ID:-unknown} ${VERSION_ID:-?}: this is only tested on Ubuntu 24.04. Continuing because of --dry-run or ROBOTEK_FORCE=1."
  [ "$DRY" = 1 ] || [ "${ROBOTEK_FORCE:-0}" = 1 ] || { echo "For the simulator on a laptop use tools/install-ubuntu.sh." >&2; exit 1; }
fi

# 2. ROS 2 Jazzy and the apt packages
if [ -f /opt/ros/jazzy/setup.bash ]; then
  say "ROS 2 Jazzy is already installed"
else
  say "Installing ROS 2 Jazzy base"
  run bash "$REPO/tools/install-ubuntu.sh" --no-gazebo
fi
say "Installing the apt packages of the car"
run sudo apt-get install -y ros-jazzy-cv-bridge ros-jazzy-robot-state-publisher ros-jazzy-xacro ros-jazzy-tf2-ros \
  python3-serial python3-lgpio python3-opencv python3-numpy python3-yaml v4l-utils

# 3. udev rules and groups
if ! pidof systemd-udevd >/dev/null 2>&1 && [ "$DRY" = 0 ]; then
  warn "systemd-udevd is not running (a container?): skipping the udev rules and the groups."
else
  say "Installing the udev rules"
  run sudo cp "$REPO/tools/99-robotek.rules" /etc/udev/rules.d/99-robotek.rules
  run sudo udevadm control --reload-rules
  run sudo udevadm trigger
  TARGET_USER="${SUDO_USER:-${USER:-}}"
  if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = root ]; then
    warn "Running as root without SUDO_USER: add the user to the groups by hand: usermod -aG dialout,video,gpio USER"
  else
    missing=""
    for group in dialout video gpio; do
      getent group "$group" >/dev/null 2>&1 || run sudo groupadd "$group"
      id -nG "$TARGET_USER" 2>/dev/null | tr ' ' '\n' | grep -qx "$group" || missing="$missing,$group"
    done
    if [ -n "$missing" ]; then
      say "Adding $TARGET_USER to the groups: ${missing#,} (log out and in again for them to count)"
      run sudo usermod -aG "${missing#,}" "$TARGET_USER"
    else
      say "$TARGET_USER is already in dialout, video and gpio"
    fi
  fi
fi

# 4. Build
if [ "$SKIP_BUILD" = 1 ]; then
  say "Skipping the build (--skip-build)"
else
  say "Building the workspace"
  if [ "$DRY" = 1 ]; then
    echo "    \$ (cd $REPO && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install)"
  else
    ( cd "$REPO" && set +u && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install )
  fi
fi

if [ "$DRY" = 1 ]; then
  say "End of --dry-run: nothing was executed."
else
  cat <<EOF

Next steps:
  1. If you were added to new groups, log out and in again.
  2. bash tools/setup-pi.sh --check           # board, LiDAR, camera and groups
  3. With the car on supports (wheels in the air):
       bash tools/obstacle-round.sh            # Obstacle Challenge
       bash tools/car-run.sh open              # Open Challenge
     The board LEDs turn green when the sensors give data; the board button is Start (a second press stops).
EOF
fi
