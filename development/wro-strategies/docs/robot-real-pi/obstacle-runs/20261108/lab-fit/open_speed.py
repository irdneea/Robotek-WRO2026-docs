"""Open v5 (car settings) on the classic field with real_v3 and a candidate high-speed table: time, laps, path, mean."""
import math, sys
from robotek_evaluation import open_lab as L
rows = []
orig = L._row
def spy(now, label, x, y, yaw, steer):
    rows.append((now, label, x, y)); return orig(now, label, x, y, yaw, steer)
L._row = spy
over = dict(inner_gap=0.35, wall_heading_gain=0.3, finish_speed=0.4, finish_lead=0.25)
for arg in sys.argv[1:]:
    hi = [float(v) for v in arg.split(',')]
    car = L.car_profile('real_v3', {'speed_table_real': [0.045, 0.09, 0.16, 0.28, 0.45] + hi, **({'drive_command_limit': float(__import__('os').environ['CAP'])} if 'CAP' in __import__('os').environ else {})})
    for direction in ('cw',):
        rows.clear()
        r = L.run_round(L.FIELDS / 'square100.sdf', direction, L.v5_factory(over), car=car)
        t_end = r['time'] or rows[-1][0]
        start = next(t for t, *_ in rows if t > 0) if rows else 0
        path = sum(math.hypot(b[2] - a[2], b[3] - a[3]) for a, b in zip(rows, rows[1:]) if b[0] <= t_end + rows[0][0] + 0.01 and b[1] not in ('IDLE',))
        print('%-12s %s t %.2f laps %s path %.1f m mean %.2f m/s turns %s %s' % (arg, direction, r['time'], [round(x, 1) for x in r['laps']], path, path / r['time'], r['turns'], r['failed']))
