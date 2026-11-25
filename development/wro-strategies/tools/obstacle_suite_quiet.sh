#!/usr/bin/env bash
# Obstacle standard set (seeds 0-4 x ccw/cw = 10 rounds) with a quality gate: wait for a quiet
# machine (load <= 4 by default; override with QUIET_LOAD) and rerun (up to 3 times) a round whose
# node fell behind the simulation: control ticks more than 0.2 s apart, or LiDAR stamps drifting
# from /clock by more than 0.1 s anywhere in the run. clean=0 rounds are kept as attempts in the ledger.
# 4, not 8 as in the Open: each Obstacle round is ~80 s of simulation and Gazebo alone adds ~4 to
# the load, so an 8 start already produced lagged rounds (22 Oct 2026).
#   tools/obstacle_suite_quiet.sh <tag> [profile.yaml] [extra runner args]
# No `set -u`: macos_env.sh sources install/setup.bash, which reads unset COLCON_TRACE.
tag=${1:?usage: obstacle_suite_quiet.sh <tag> [profile.yaml] [extra runner args]}; shift
profile=src/robotek_obstacle/config/obstacle_v3.yaml   # v3; obstacle_sensors_v1.yaml needs --strategy current
if [ $# -gt 0 ] && [ "${1##*.}" = yaml ]; then profile=$1; shift; fi
cd "$(dirname "$0")/.."
source tools/macos_env.sh >/dev/null 2>&1; source install/setup.sh >/dev/null 2>&1
load1() { if [ -r /proc/loadavg ]; then cut -d' ' -f1 /proc/loadavg | cut -d. -f1; else sysctl -n vm.loadavg | awk '{gsub(/[{}]/,""); print int($1)}'; fi; }
quiet() { while :; do [ "$(load1)" -le "${QUIET_LOAD:-4}" ] && return; sleep 20; done; }
for seed in 0 1 2 3 4; do
  for dir in ccw cw; do
    for attempt in 1 2 3; do
      quiet
      bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh \
        --name "$tag-reg$seed-$dir" --seed "$seed" --direction "$dir" --profile "$profile" \
        --steer-p-gain 20 --launch-arg real_car:=true \
        --no-gui --no-rviz --real-time-factor 2 --wall-timeout 320 "$@" >/dev/null 2>&1
      d=$(ls -dt docs/obstacle-challenge-runs/*-"$tag"-reg"$seed"-"$dir" 2>/dev/null | head -1)
      ok=$(python3 - "$d" <<'PY'
import csv, gzip, json, sys
d = sys.argv[1]
try:
    rows = list(csv.DictReader(open(d + '/telemetry.csv')))
    t = [float(r['sim_time']) for r in rows]
    dd = [b - a for a, b in zip(t, t[1:]) if 0 < b - a < 1]
    lag = []
    with gzip.open(d + '/scans.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            lag.append(r['stamp'] - r['sim_time'])
    ok = bool(dd) and max(dd) <= 0.2 and max(lag[10:]) < 0.1 and min(lag[10:]) > -0.1
    print('1' if ok else '0')
except Exception:
    print('0')
PY
)
      python3 - "$d" "$ok" "$attempt" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1] + '/round.json'))
except Exception:
    print('%-46s (no round.json) clean=%s attempt=%s' % (sys.argv[1].split('/')[-1], sys.argv[2], sys.argv[3]), flush=True)
    raise SystemExit
v = r.get('validation') or {}
g = r.get('rule_judge') or {}
print('%-46s pts=%-3s t=%-7s valid=%-5s %-9s clean=%s attempt=%s %s' % (
    sys.argv[1].split('/')[-1], r.get('points_estimated'),
    '%.2f' % g['time_from_start_sim_seconds'] if g.get('time_from_start_sim_seconds') else '-',
    v.get('passed'), v.get('margin_class'), sys.argv[2], sys.argv[3],
    ','.join(v.get('failed', []))), flush=True)
PY
      [ "$ok" = 1 ] && break
    done
  done
done
