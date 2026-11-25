"""real_v3 servo: 10/50/90 % of full-lock yaw rate after a step, release 50 %, and the round-2 flip (4 nov)."""
import math, sys
from robotek_evaluation.open_lab import Actuators, car_profile
name = sys.argv[1] if len(sys.argv) > 1 else 'real_v3'
p = dict(car_profile(name)['actuator'], drive_delay=0.0, drive_tau=0.0, accel_max=50, decel_max=50)
def run(cmds, v, tend, dt=0.001):
    a = Actuators(p); out = []; t = 0.0
    while t < tend:
        steer = cmds(t); a.command(t, v, steer); vo, r = a.step(t, dt); out.append((t, r, vo)); t += dt
    return out
out = run(lambda t: 0.0 if t < 0.5 else -0.307, 0.57, 1.5)
full = min(r for _, r, _ in out)
for f in (0.1, 0.5, 0.9):
    print('%s: %d %% at +%.3f s' % (name, f * 100, next(t for t, r, _ in out if r <= f * full) - 0.5))
out = run(lambda t: -0.307 if t < 1.0 else 0.0, 0.57, 2.0)
print('release 50 %% at +%.3f s' % (next(t for t, r, _ in out if t > 1.0 and r >= 0.5 * full) - 1.0))
p.update(speed_table_cmd=[0.0], speed_table_real=[0.0], drive_command_limit=0.0)
for v in (0.2, 0.3, 0.57, 0.70, 0.80, 0.87):
    o = run(lambda t: -0.307, v, 1.0); r = -o[-1][1]
    print('real v %.2f: full-lock yaw %.2f rad/s, radius %.3f m' % (o[-1][2], r, o[-1][2] / r))
# round 2 of 4 nov, cmd_vel_raw (v, wz) samples -> strategy angle with the real wheelbase 0.1174
R2 = [(1.0, 0.15, -0.41), (1.055, 0.30, -0.81), (1.243, 0.20, -0.54), (1.364, 0.20, -0.49), (1.426, 0.20, -0.04),
      (1.489, 0.20, 0.17), (1.553, 0.20, 0.54), (2.0, 0.20, 0.54)]
def r2(t):
    v, wz = [(v, w) for t0, v, w in R2 if t0 <= t][-1] if t >= 1.0 else (0.15, -0.41)
    return max(-0.307, min(0.307, math.atan(wz * 0.1174 / v)))
o = run(r2, 0.38, 2.0)
print('r2 flip: gyro zero crossing at %.3f s (real 1.64-1.65; command crosses 0 at ~1.43)' % next(t for t, r, _ in o if t > 1.3 and r >= 0))
