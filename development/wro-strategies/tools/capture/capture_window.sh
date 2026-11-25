#!/usr/bin/env bash
# Capture one on-screen window to a PNG (macOS). Gazebo and RViz cannot be driven by computer use, so capture them
# by window id with the system screencapture (needs Screen Recording permission for the app that runs this).
#   tools/capture/capture_window.sh <owner-or-title-substring> <out.png>      e.g.  gz  img/02-gazebo.png
#   tools/capture/capture_window.sh --list [substring]                         list candidate windows
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = "--list" ]; then swift "$here/list_windows.swift" "${2:-}"; exit 0; fi
id=$(swift "$here/list_windows.swift" "$1" | head -1 | cut -f1)
[ -n "$id" ] || { echo "no window matches '$1' (try --list)" >&2; exit 1; }
screencapture -x -o -l "$id" "$2"
echo "captured window $id -> $2"
