#!/usr/bin/env bash
# Small, progressive changes of start position; all attempts use the recorded runner.
set -euo pipefail
tag=${1:?tag}; profile=${2:?profile}; stage=${3:-1}; field=${4:-square100}
cd "$(dirname "$0")/.."
world="docs/open-challenge-runs/field-size-driver/worlds/$field.sdf"
test -f "$world"
field_tag=$field
if [ "$field" = square100 ]; then field_tag=sq100; fi
case "$stage" in
  1) cases=("xp10 0.10 -1.15" "xm10 -0.10 -1.15") ;;
  2) cases=("yp05 0.0 -1.10" "ym05 0.0 -1.20") ;;
  3) cases=("xp25 0.25 -1.15" "xm25 -0.25 -1.15" "yp15 0.0 -1.0" "ym15 0.0 -1.30") ;;
  *) echo "Stage must be 1, 2 or 3" >&2; exit 2 ;;
esac
for spec in "${cases[@]}"; do
  read -r label sx sy <<< "$spec"
  for direction in ccw cw; do
    yaw=0.0
    if [ "$direction" = cw ]; then yaw=3.141592653589793; fi
    name="realcar-starts-$tag-$field_tag-$label-$direction"
    bash src/robotek_evaluation/tools/run_gui_experiment.sh "$name" \
      --params-file "$profile" \
      --world "$world" \
      --direction "$direction" --controller-direction auto \
      --spawn-x "$sx" --spawn-y "$sy" --spawn-yaw "$yaw" \
      --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 \
      --launch-arg real_car:=true --no-gui --real-time-factor 0 \
      > "/tmp/$name.log" 2>&1
    python3 - "$name" <<'PY'
import json,sys
from pathlib import Path
p=sorted(Path('docs/open-challenge-runs').glob('*-'+sys.argv[1]))[-1]
r=json.loads((p/'round.json').read_text());j=r.get('rule_judge') or {};v=r.get('validation') or {}
print(p.name, 'points=',r['points_estimated'], 'sim=',j.get('time_from_start_sim_seconds'),
      'valid=',v.get('passed'), 'failed=',v.get('failed'), flush=True)
PY
  done
done
