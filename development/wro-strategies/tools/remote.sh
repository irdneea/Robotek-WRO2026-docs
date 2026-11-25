#!/usr/bin/env bash
# Heavy runs on the remote machine (decision of the user, 26 Oct 2026): headless Gazebo rounds, the
# Open and Obstacle labs and the quiet suites run there, not on the Mac. GUI rounds stay on the Mac.
#
#   tools/remote.sh sync              # copy the Mac's working tree (uncommitted changes too) and build
#   tools/remote.sh run <command...>  # run from the remote repo root, ROS Jazzy sourced, in bash
#   tools/remote.sh run 'a && b'      # one argument: a shell line
#   tools/remote.sh fetch             # bring the new rounds back and append their ledger lines here
#
# Typical: tools/remote.sh sync && tools/remote.sh run python3 tools/obstacle_lab_suite.py --seeds 0-4
#          tools/remote.sh run tools/obstacle_suite_quiet.sh <tag> && tools/remote.sh fetch
# The remote is WSL2 Ubuntu 24.04 with ROS Jazzy from apt (Tailscale SSH); see docs/maquina-remota.md.
# `sync` fetches first and then puts these ledgers on the remote, so `fetch` appends exactly the
# remote's new lines. Fetch before running rounds on the Mac again.
set -eo pipefail
REMOTE=${REMOTE:-REMOTE_HOST}
REMOTE_DIR=${REMOTE_DIR:-Projects/WRO-Strategies}
LEDGERS="docs/open-challenge-runs/rounds.jsonl docs/obstacle-challenge-runs/rounds.jsonl"
cd "$(dirname "$0")/.."

remote() { ssh -o BatchMode=yes "$REMOTE" "bash -lc $(printf '%q' "cd $REMOTE_DIR && source /opt/ros/jazzy/setup.bash && { [ ! -f install/setup.bash ] || source install/setup.bash; } && $*")"; }

case ${1:-} in
  sync)
    # Fetch first: the rsync below puts this ledger on the remote, which would drop its new lines.
    "$0" fetch
    # Round folders stay where they ran; src and tools mirror the Mac exactly.
    rsync -a --exclude .git --exclude /build --exclude /install --exclude /log --exclude __pycache__ \
      --exclude '/docs/*-challenge-runs/2*/' --exclude /Robotek-WRO2026 --exclude /plans ./ "$REMOTE:$REMOTE_DIR/"
    rsync -a --delete --exclude __pycache__ src tools "$REMOTE:$REMOTE_DIR/"
    remote "colcon build --symlink-install 2>&1 | tail -2"
    ;;
  run)
    shift
    # One argument is a shell line ('a && b'); several are a command and its arguments.
    if [ $# -eq 1 ]; then remote "$1"; else remote "$(printf '%q ' "$@")"; fi
    ;;
  fetch)
    for dir in docs/open-challenge-runs docs/obstacle-challenge-runs; do
      rsync -a --ignore-existing --exclude rounds.jsonl "$REMOTE:$REMOTE_DIR/$dir/" "$dir/"
    done
    for ledger in $LEDGERS; do
      n=$(wc -l < "$ledger")
      ssh -o BatchMode=yes "$REMOTE" "tail -n +$((n + 1)) $REMOTE_DIR/$ledger" | python3 -c '
import json, sys
host = sys.argv[1]
for line in sys.stdin:
    if line.strip():
        round_ = json.loads(line)
        round_.setdefault("host", host)
        print(json.dumps(round_, ensure_ascii=False))
' "$REMOTE (WSL2 Ubuntu 24.04, ROS Jazzy apt)" | tee -a "$ledger" | python3 -c '
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print("fetched", r.get("name") or r.get("run"), "pts", r.get("points_estimated"))
'
      rsync -a "$ledger" "$REMOTE:$REMOTE_DIR/$ledger"
    done
    ;;
  *)
    sed -n 2,14p "$0"; exit 2 ;;
esac
