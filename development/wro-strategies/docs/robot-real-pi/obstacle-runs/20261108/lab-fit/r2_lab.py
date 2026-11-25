import sys, math
from robotek_evaluation import obstacle_lab as L
from robotek_evaluation.open_lab import car_profile
rows = []
orig = L._row
def spy(now, label, x, y, yaw, steer, direction):
    rows.append((now, label, x, y, yaw, steer)); return orig(now, label, x, y, yaw, steer, direction)
L._row = spy
car = None if sys.argv[1] == 'gazebo' else car_profile(sys.argv[1], {k: __import__('yaml').safe_load(v) for k, v in (a.split('=', 1) for a in sys.argv[3:] if '=' in a and not a.startswith('p:'))})
over = {a[2:].split('=')[0]: float(a[2:].split('=')[1]) for a in sys.argv[3:] if a.startswith('p:')}
r = L.run_round('/tmp/obslab/real-r2-cw', strategy_name='v3', tmax=float(sys.argv[2]), car=car, overrides=over)
print({k: v for k, v in r.items() if not isinstance(v, (list, dict)) or k in ('contact',)})
t0 = next((t for t, lab, *_ in rows if lab == 'RUN'), None); step = 0
for t, lab, x, y, yaw, steer in rows:
    if t0 is not None and t - t0 >= step and t - t0 < 5.0:
        # heading relative to the lane (cw drives toward -x): + = toward the island (+y)
        rel = -math.degrees(math.atan2(math.sin(yaw - math.pi), math.cos(yaw - math.pi)))
        print('t %.2f %-6s x %.3f y %.3f heading-to-island %+5.1f steer %+5.1f island gap %.3f' % (t - t0, lab, x, y, rel, math.degrees(steer), -0.5 - y))
        step += 0.05
