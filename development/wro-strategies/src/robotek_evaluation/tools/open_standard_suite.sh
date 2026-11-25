#!/usr/bin/env bash
# Open Challenge standard validation set: 6 fields x 2 directions, same start for every profile.
#   open_standard_suite.sh <tag> <profile.yaml> [extra run_gui_experiment args...]
# Runs Open v5, the only strategy. Prefer tools/open_suite_quiet.sh (it waits for a quiet machine).
# Rounds are named std12-<tag>-<field>-<dir>; use the same tag for one profile/servo pair.
set -u
tag=$1; profile=$2; shift 2
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
worlds="$root/docs/open-challenge-runs/field-size-driver/worlds"
for field in square100 square180 rect100x180 rect180x100 shift140 east140x100; do
  for dir in ccw cw; do
    if [ "$dir" = cw ]; then yaw=3.141592653589793; else yaw=0.0; fi
    bash "$here/run_gui_experiment.sh" "std12-$tag-$field-$dir" --params-file "$profile" \
      --world "$worlds/$field.sdf" --direction "$dir" --controller-direction auto \
      --spawn-x 0.0 --spawn-y -1.15 --spawn-yaw "$yaw" --ackermann-velocity-limit 4.0 "$@" > /dev/null 2>&1
    d=$(ls -dt "$root"/docs/open-challenge-runs/*-std12-"$tag-$field-$dir" | head -1)
    python3 - "$d" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]+'/round.json')); v = r.get('validation') or {}; g = r.get('rule_judge') or {}
print('%-46s pts=%-3s t=%-7s valid=%-5s %-12s %s' % (sys.argv[1].split('/')[-1][17:], r.get('points_estimated'),
      '%.2f' % g['time_from_start_sim_seconds'] if g.get('time_from_start_sim_seconds') else '-', v.get('passed'),
      v.get('margin_class'), ','.join(v.get('failed', []))), flush=True)
PY
  done
done
