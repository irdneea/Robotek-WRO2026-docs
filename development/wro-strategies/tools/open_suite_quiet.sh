#!/usr/bin/env bash
# Open standard set (12 rounds) for the v5 strategy with a quality gate: wait for a quiet machine (load <= 8),
# and rerun (up to 3 times) a round whose node fell behind the simulation: control ticks more than 0.2 s apart or
# LiDAR stamps drifting from /clock by more than 0.1 s anywhere in the run. clean=0 rounds are kept as attempts.
#   tools/open_suite_quiet.sh <tag>
tag=$1; shift
cd "$(dirname "$0")/.."
source tools/macos_env.sh >/dev/null 2>&1; source install/setup.sh >/dev/null 2>&1
W=docs/open-challenge-runs/field-size-driver/worlds
load1() { if [ -r /proc/loadavg ]; then cut -d' ' -f1 /proc/loadavg | cut -d. -f1; else sysctl -n vm.loadavg | awk '{gsub(/[{}]/,""); print int($1)}'; fi; }
quiet() { while :; do [ "$(load1)" -le 8 ] && return; sleep 20; done; }
for field in square100 square180 rect100x180 rect180x100 shift140 east140x100; do
  for dir in ccw cw; do
    yaw=0.0; [ $dir = cw ] && yaw=3.141592653589793
    for attempt in 1 2 3; do
      quiet
      bash src/robotek_evaluation/tools/run_gui_experiment.sh "std12-$tag-$field-$dir" --strategy v5 --params-file src/robotek_open/config/open_v5.yaml --world $W/$field.sdf --direction $dir --controller-direction auto --spawn-x 0.0 --spawn-y -1.15 --spawn-yaw $yaw --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 --launch-arg real_car:=true --no-gui --real-time-factor 2 >/dev/null 2>&1
      d=$(ls -dt docs/open-challenge-runs/*-std12-$tag-$field-$dir | head -1)
      ok=$(python3 - "$d" <<'PY'
import csv,gzip,json,sys,numpy as np
d=sys.argv[1]
try:
    T=np.array([float(r['sim_time']) for r in csv.DictReader(open(d+'/telemetry.csv'))]); dd=np.diff(T[T>1]); dd=dd[dd<1]
    lag=[]
    for i,l in enumerate(gzip.open(d+'/telemetry.csv.scans.jsonl.gz','rt')):
        r=json.loads(l); lag.append(r['stamp']-r['sim_time'])
    print('1' if len(dd) and dd.max()<=0.2 and max(lag[10:])<0.1 and min(lag[10:])>-0.1 else '0')
except Exception: print('0')
PY
)
      python3 - "$d" "$ok" "$attempt" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]+'/round.json')); v=r.get('validation') or {}; g=r.get('rule_judge') or {}
print('%-46s pts=%-3s t=%-7s valid=%-5s %-12s clean=%s attempt=%s %s'%(sys.argv[1].split('/')[-1][17:],r.get('points_estimated'),'%.2f'%g['time_from_start_sim_seconds'] if g.get('time_from_start_sim_seconds') else '-',v.get('passed'),v.get('margin_class'),sys.argv[2],sys.argv[3],','.join(v.get('failed',[]))),flush=True)
PY
      [ "$ok" = 1 ] && break
    done
  done
done
