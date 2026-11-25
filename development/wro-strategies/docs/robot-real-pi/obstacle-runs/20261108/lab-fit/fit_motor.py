"""Fit board motor dead time / lag / accel to the 8 nov SDK pulse tests (54:30, M2, no motor type)."""
import itertools, sys
sys.path.insert(0, 'src/robotek_evaluation'); sys.path.insert(0, 'src/robotek_common')
from robotek_evaluation.open_lab import Actuators, actuator_parameters
# (cmd m/s = rps/4.4, duration s, moved m, rolled m) forward and backward averaged where repeated
DATA = [(1/4.4, 1.0, 0.11, 0.12), (1/4.4, 1.0, 0.13, 0.09), (2/4.4, 1.0, 0.16, 0.14), (3/4.4, 1.0, 0.23, 0.13),
        (1/4.4, 1.0, 0.09, 0.13), (1/4.4, 1.0, 0.12, 0.10), (2/4.4, 1.0, 0.20, 0.14), (3/4.4, 1.0, 0.19, 0.16),
        (0.5/4.4, 2.0, 0.13, 0.065), (0.2/4.4, 5.0, 0.17, 0.025), (0.3/4.4, 3.3, 0.16, 0.045), (0.4/4.4, 2.5, 0.145, 0.055),
        (0.6/4.4, 1.7, 0.145, 0.055), (0.7/4.4, 1.4, 0.145, 0.07), (0.8/4.4, 1.2, 0.125, 0.09), (0.9/4.4, 1.1, 0.125, 0.10)]
TABLE = ([0.05, 0.10, 0.165, 0.33, 0.55, 1.0], [0.045, 0.09, 0.16, 0.28, 0.45, 0.82])

def simulate(p, cmd, dur):
    a = Actuators(p); dt = 0.005; t = 0.0; x = 0.0; moved = None
    while t < dur + 1.0:
        a.command(t, cmd if t < dur else 0.0, 0.0)
        v, _ = a.step(t, dt); x += v * dt; t += dt
        if moved is None and t >= dur: moved = x
    return moved, x - moved

def cost(p):
    e = 0.0
    for cmd, dur, m, r in DATA:
        sm, sr = simulate(p, cmd, dur); e += (sm - m) ** 2 + (sr - r) ** 2
    return (e / len(DATA)) ** 0.5

base = actuator_parameters(); base.update(wheelbase=0.11883, steer_limit=0.33, speed_table_cmd=TABLE[0],
                                          speed_table_real=TABLE[1], decel_max=50.0, drive_command_limit=0.0)
best = []
for d, tau, acc in itertools.product([0.05, 0.1, 0.15, 0.2, 0.25, 0.3], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 50]):
    p = dict(base, drive_delay=d, drive_tau=tau, accel_max=acc)
    best.append((cost(p), d, tau, acc))
best.sort()
for row in best[:8]: print('rms %.4f m  delay %.2f tau %.2f accel %.1f' % row)
c, d, tau, acc = best[0]
p = dict(base, drive_delay=d, drive_tau=tau, accel_max=acc)
for cmd, dur, m, r in DATA:
    sm, sr = simulate(p, cmd, dur); print('cmd %.3f %4.1f s: moved %.3f (real %.3f) rolled %.3f (real %.3f)' % (cmd, dur, sm, m, sr, r))
