#!/usr/bin/env bash
# Run several recorded Obstacle rounds (regulation layouts) one after another.
#   [STRATEGY=v3|v2|current] run_obstacle_batch.sh <name-prefix> <profile.yaml> "<seeds>" "<directions>" [extra runner args]
set -u
prefix=$1; profile=$2; seeds=$3; directions=$4; shift 4
here="$(dirname "$0")"
for d in $directions; do
  for s in $seeds; do
    bash "$here/run_obstacle_gui_experiment.sh" --name "${prefix}-reg${s}-${d}" \
      --seed "$s" --direction "$d" --profile "$profile" --strategy "${STRATEGY:-v3}" --wall-timeout 320 "$@" 2>&1 | grep '^{' | cut -c1-400
  done
done
