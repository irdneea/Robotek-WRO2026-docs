import csv, glob, math, statistics as s, os
runs = sorted(glob.glob('/tmp/opencrash/2026*/telemetry.csv'))
curv, delays, speeds, ratio = [], [], [], []
for f in runs:
    rows = list(csv.DictReader(open(f)))
    g = lambda r, k: float(r[k]) if r[k] not in ('', 'inf', 'nan') else math.nan
    T = [(g(r,'wall_time'), r['state'], g(r,'v_cmd'), g(r,'w_cmd'), g(r,'gyro'), g(r,'travelled'), g(r,'yaw_imu')) for r in rows]
    for i in range(1, len(T)):
        t, st, v, w, gz, tr, yaw = T[i]
        tp, _, _, _, _, trp, yawp = T[i-1]
        dt = t - tp
        if dt <= 0 or dt > 0.1: continue
        vr = (tr - trp)/dt
        # steady full-lock arcs: TURN, |w| at full lock, real speed > 0.3
        if st == 'TURN' and abs(w) > 1.9 and vr > 0.3 and abs(gz) > 0.3:
            curv.append(abs(gz)/vr); speeds.append(vr); ratio.append(vr/v if v > 0 else math.nan)
    # delay: from first TURN tick to gyro reaching 50 % of its turn plateau
    for i in range(1, len(T)):
        if T[i][1] == 'TURN' and T[i-1][1] != 'TURN':
            t0 = T[i][0]; seg = [x for x in T[i:i+60] if x[1] == 'TURN']
            if len(seg) < 15: continue
            plateau = s.median(abs(x[4]) for x in seg[8:15])
            hit = next((x[0]-t0 for x in seg if abs(x[4]) >= 0.5*plateau), None)
            if hit is not None and plateau > 0.5: delays.append(hit)
print('arcs: curvature (1/m) median %.2f (p10 %.2f, p90 %.2f) -> radius %.3f m; model full lock 17.5 deg: %.2f 1/m (R %.3f)' % (
    s.median(curv), sorted(curv)[len(curv)//10], sorted(curv)[9*len(curv)//10], 1/s.median(curv), math.tan(0.3054)/0.11883, 0.11883/math.tan(0.3054)))
print('arc real speed median %.2f m/s, real/commanded %.2f' % (s.median(speeds), s.median([r for r in ratio if r == r])))
print('turn start -> 50 %% yaw rate: median %.2f s (n %d, p90 %.2f)' % (s.median(delays), len(delays), sorted(delays)[9*len(delays)//10]))
# straights: real vs commanded speed
st = []
for f in runs:
    rows = list(csv.DictReader(open(f)))
    for a, b in zip(rows, rows[1:]):
        try:
            dt = float(b['wall_time'])-float(a['wall_time']); vr = (float(b['travelled'])-float(a['travelled']))/dt; v = float(b['v_cmd'])
        except Exception: continue
        if b['state'] == 'FOLLOW' and 0 < dt < 0.1 and v > 0.9 and b['lidar_odom_quality'].startswith('lidar'): st.append(vr)
print('straights at ~1.02 asked: real median %.2f m/s (n %d)' % (s.median(st), len(st)))
bins = {}
for f in runs:
    rows = list(csv.DictReader(open(f)))
    for a, b in zip(rows, rows[1:]):
        try:
            dt = float(b['wall_time'])-float(a['wall_time']); vr = (float(b['travelled'])-float(a['travelled']))/dt
            gz, w = abs(float(b['gyro'])), abs(float(b['w_cmd']))
        except Exception: continue
        if b['state'] == 'TURN' and w > 1.9 and 0 < dt < 0.1 and vr > 0.2 and gz > 0.3:
            bins.setdefault(round(vr*5)/5, []).append(gz/vr)
for k in sorted(bins):
    if len(bins[k]) >= 8: print('arc speed %.1f m/s: curvature %.2f 1/m (R %.2f m), n %d, implied understeer %.2f' % (k, s.median(bins[k]), 1/s.median(bins[k]), len(bins[k]), (2.57/s.median(bins[k]) - 1)/max(k*k, 0.01)))
