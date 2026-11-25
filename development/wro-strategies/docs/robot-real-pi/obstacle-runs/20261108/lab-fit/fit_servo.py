"""Fit steer_delay / steer_rate / steer_tau (servo range 0.307) to tests 11/13 (4 nov) and the round-2 flip."""
import itertools, math
from robotek_evaluation.open_lab import Actuators, car_profile
base = dict(car_profile('real_v3')['actuator'], drive_delay=0.0, drive_tau=0.0, accel_max=50, decel_max=50,
            speed_table_cmd=[0.0], speed_table_real=[0.0], drive_command_limit=0.0, understeer=0.0)
R2 = [(1.0, 0.15, -0.41), (1.055, 0.30, -0.81), (1.220, 0.20, -0.54), (1.364, 0.20, -0.49), (1.385, 0.20, -0.40),
      (1.426, 0.20, -0.04), (1.450, 0.20, 0.04), (1.470, 0.20, 0.17), (1.513, 0.20, 0.19), (1.533, 0.20, 0.54)]
def r2(t):
    v, wz = [(v, w) for t0, v, w in R2 if t0 <= t][-1] if t >= 1.0 else (0.15, -0.41)
    return max(-0.307, min(0.307, math.atan(wz * 0.1174 / v)))
def run(p, cmds, tend, v=0.5, dt=0.002):
    a = Actuators(p); out = []; t = 0.0
    while t < tend:
        a.command(t, v, cmds(t)); _, r = a.step(t, dt); out.append((t, r)); t += dt
    return out
def metrics(p):
    o = run(p, lambda t: 0.0 if t < 0.5 else -0.307, 1.5); full = min(r for _, r in o)
    m = [next(t for t, r in o if r <= f * full) - 0.5 for f in (0.1, 0.5, 0.9)]
    o = run(p, lambda t: -0.307 if t < 1.0 else 0.0, 2.0)
    m.append(next(t for t, r in o if t > 1.0 and r >= 0.5 * full) - 1.0)
    o = run(p, r2, 2.0); m.append(next(t for t, r in o if t > 1.3 and r >= 0))
    return m
TARGET = [0.135, 0.20, 0.295, 0.165, 1.66]
res = []
for d, rate, tau in itertools.product([0.06, 0.08, 0.10, 0.12], [1.4, 1.66, 2.0, 2.5, 3.0, 4.0], [0.03, 0.05, 0.07, 0.09]):
    p = dict(base, steer_delay=d, steer_rate=rate, steer_tau=tau); m = metrics(p)
    res.append((math.sqrt(sum((a - b) ** 2 for a, b in zip(m, TARGET)) / 5), d, rate, tau, m))
res.sort(key=lambda r: r[0])
for e, d, rate, tau, m in res[:8]:
    print('rms %.3f  delay %.2f rate %.2f tau %.2f  -> 10/50/90 %.3f %.3f %.3f release %.3f r2 zero %.3f' % (e, d, rate, tau, *m))
p = dict(base); print('current', ['%.3f' % x for x in metrics(p)])
