#!/usr/bin/env bash
# Ablation of Obstacle parameters in Gazebo (4 rounds per piece), for docs/obstacle-reimpl-v2.md.
# Only parameters declared in ObstacleConfig can be changed here. Fixed values (ClassVar:
# plan_loc_gain, plan_side_cost, plan_view_gain, plan_steps, plan_beam, recover, ...) need a
# temporary patch in a branch, never in main (docs/obstacle-reimpl-plan.md, fase 1).
# Output: one line per round. Run only with no other batch running; quiet machine, no GUI.
#   tools/obstacle_param_ablation.sh [tag]
tag=${1:-abl}
only=${2:-}
cd "$(dirname "$0")/.."
source tools/macos_env.sh >/dev/null 2>&1; source install/setup.sh >/dev/null 2>&1
quiet() { while :; do l=$(sysctl -n vm.loadavg | awk '{gsub(/[{}]/,""); print int($1)}'); [ "$l" -le "${QUIET_LOAD:-6}" ] && return; sleep 20; done; }
P=src/robotek_obstacle/config/obstacle_sensors_v1.yaml
declare -a AB=(
  "base:"
  "marginsup:plan_wall_margin=0.05 plan_pillar_margin=0.06 plan_soft=0.07"
  "speed035:plan_speed=0.35"
)
for item in "${AB[@]}"; do
  name=${item%%:*}; params=${item#*:}
  [ -n "$only" ] && [ "$name" != "$only" ] && continue
  pargs=(); for p in $params; do pargs+=(--param "$p"); done
  for sd in 0:ccw 1:cw 2:ccw 3:cw; do
    seed=${sd%%:*}; dir=${sd#*:}
    quiet
    bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh \
      --name "$tag-$name-reg$seed-$dir" --seed "$seed" --direction "$dir" --profile "$P" --strategy current \
      --steer-p-gain 20 --launch-arg real_car:=true --no-gui --no-rviz \
      --real-time-factor 1 --wall-timeout 320 "${pargs[@]}" >/dev/null 2>&1
    d=$(ls -dt docs/obstacle-challenge-runs/*-"$tag"-"$name"-reg"$seed"-"$dir" 2>/dev/null | head -1)
    python3 - "$d" "$name" <<'PY'
import json, sys
r = json.load(open(sys.argv[1] + '/round.json'))
v = r.get('validation') or {}
g = r.get('rule_judge') or {}
print('%-10s %-20s pts=%-3s t=%-7s valid=%-5s %-9s m=%-6s %s' % (
    sys.argv[2], sys.argv[1].split('/')[-1].split('-reg', 1)[-1],
    r.get('points_estimated'),
    '%.2f' % g['time_from_start_sim_seconds'] if g.get('time_from_start_sim_seconds') else '-',
    v.get('passed'), v.get('margin_class'),
    '%.1fcm' % (v['min_clearance_m'] * 100) if v.get('min_clearance_m') else '-',
    ','.join(v.get('failed', []))), flush=True)
PY
  done
done
