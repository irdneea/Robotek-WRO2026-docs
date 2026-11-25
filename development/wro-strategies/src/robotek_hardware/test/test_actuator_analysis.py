import csv
import math

import numpy as np

from robotek_hardware.actuator_analysis import WHEELBASE, analyse, speeds, step_response

IMU_DT, SCAN_DT = 1/49, .1


def first_order(t, t0, delay, tau, gain):
    x = np.clip(t-t0-delay, 0., None)
    return gain*(1-np.exp(-x/tau))


def pulse_speed(t, t0, t_off, delay=.08, tau=.2, top=.9, coast_tau=.4):
    """Speed of a 0.25 s motor pulse: first-order rise, exponential coast after the cut."""
    rise = first_order(t, t0, delay, tau, top)
    at_off = float(first_order(np.array([t_off]), t0, delay, tau, top)[0])
    coast = at_off*np.exp(-np.clip(t-t_off, 0., None)/coast_tau)
    return np.where(t < t_off, rise, coast)


def write(path, header, rows):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def test_step_response_recovers_delay_and_time_constant():
    rng = np.random.default_rng(1)
    t = np.arange(0., 3., IMU_DT)
    y = first_order(t, 1., .10, .15, 2.)+rng.normal(0., .01, t.size)
    r = step_response(t, y, 1., 3., k=4., min_delta=.05)
    assert abs(r['delay']-.10) < 2*IMU_DT
    assert abs(r['tau']-.15) < 2*IMU_DT
    assert abs(r['final']-2.) < .05


def test_speeds_from_a_wall_approaching_at_constant_speed():
    t = np.arange(0., 2., SCAN_DT)
    v = speeds(t, 3.-.5*t)
    assert np.allclose(v[2:-2], .5, atol=1e-6)


def test_short_motor_pulse_and_coasting_turn(tmp_path):
    rng = np.random.default_rng(2)
    angle = 20.
    # plan: idle 0-1, motor pulse 1-1.24 (cut row), motor 0 until 3.25,
    #       wheels to +20 3.25-4.25, pulse 4.25-4.49 (cut), coast until 5.75, centre 5.75-6.75
    commands = [(0., 'inicio', 'idle', 0., 1500, 0.), (1., 'motor 30%', 'motor', 0., 1500, 30.),
                (1.24, 'corte 0.25 s', 'motor', 0., 1500, 0.), (1.25, 'motor 0', 'motor', 0., 1500, 0.),
                (3.25, 'ruedas a +20', 'turn_pre', angle, 1880, 0.),
                (4.25, 'giro +20', 'turn', angle, 1880, 30.),
                (4.49, 'corte 0.25 s', 'turn', angle, 1880, 0.),
                (4.5, 'giro +20 sin motor', 'turn_coast', angle, 1880, 0.),
                (5.75, 'centrar', 'turn_post', 0., 1500, 0.), (6.75, 'fin', 'idle', 0., 1500, 0.)]
    write(tmp_path/'commands.csv', ['t', 'step', 'phase', 'servo_deg', 'servo_us', 'motor_pct'], commands)
    t = np.arange(0., 6.75, IMU_DT)
    speed = pulse_speed(t, 1., 1.24)+pulse_speed(t, 4.25, 4.49)
    steer = np.radians(first_order(t, 3.25, .06, .1, angle)-first_order(t, 5.75, .06, .1, angle))
    gz = speed*np.tan(steer)/WHEELBASE+rng.normal(0., .005, t.size)
    accel = np.gradient(speed, t)+rng.normal(0., .02, t.size)
    zeros = np.zeros(t.size)
    write(tmp_path/'imu.csv', ['t', 'gx', 'gy', 'gz', 'ax', 'ay', 'az'],
          zip(t, zeros, zeros, gz, zeros, accel, zeros+9.8))   # forward = board +y
    ts = np.arange(0., 6.75, SCAN_DT)
    position = np.interp(ts, t, np.cumsum(speed)*IMU_DT)
    front = 4.-position+rng.normal(0., .002, ts.size)
    write(tmp_path/'scan.csv', ['t', 'front', 'front_min'], zip(ts, front, front))

    steps = {s['step']: s for s in analyse(str(tmp_path))['steps']}
    motor = steps['motor 30%']
    assert motor['se_mueve']
    assert abs(motor['pulso_s']-.24) < 1e-6
    assert motor['delay_movimiento_lidar_s'] is not None
    assert motor['distancia_total_m'] > .1
    assert abs(motor['delay_aceleracion_s']-.08) < 3*IMU_DT
    true_peak = float(pulse_speed(np.array([1.24]), 1., 1.24)[0])
    assert abs(motor['velocidad_max_imu_mps']-true_peak) < .05
    assert motor['velocidad_max_lidar_mps'] <= true_peak+.02   # smoothed: never above
    turn = steps['giro +20']
    assert abs(turn['angulo_por_rumbo_deg']-angle) < 2.
    assert abs(turn['angulo_instantaneo_deg']-angle) < 2.
    assert turn['signo_ok']


def test_long_pulses_give_cruise_speed_and_wheel_angle(tmp_path):
    rng = np.random.default_rng(3)
    angle, top = 20., .3
    # straight 1 s pulse at 20 % (1-2), stop; wheels to +20 (4-5), 1 s pulse (5-6), coast, centre
    commands = [(0., 'inicio', 'idle', 0., 1500, 0.), (1., 'motor 20%', 'motor', 0., 1500, 20.),
                (2., 'motor 0', 'motor', 0., 1500, 0.), (4., 'ruedas a +20', 'turn_pre', angle, 1880, 0.),
                (5., 'giro +20', 'turn', angle, 1880, 20.), (6., 'giro +20 sin motor', 'turn_coast', angle, 1880, 0.),
                (7.5, 'centrar', 'turn_post', 0., 1500, 0.), (8.5, 'fin', 'idle', 0., 1500, 0.)]
    write(tmp_path/'commands.csv', ['t', 'step', 'phase', 'servo_deg', 'servo_us', 'motor_pct'], commands)
    t = np.arange(0., 8.5, IMU_DT)
    speed = pulse_speed(t, 1., 2., top=top, tau=.15)+pulse_speed(t, 5., 6., top=top, tau=.15)
    steer = np.radians(np.where((t >= 4.1) & (t < 7.5), angle, 0.))
    gz = speed*np.tan(steer)/WHEELBASE+rng.normal(0., .005, t.size)
    zeros = np.zeros(t.size)
    write(tmp_path/'imu.csv', ['t', 'gx', 'gy', 'gz', 'ax', 'ay', 'az'],
          zip(t, zeros, zeros, gz, zeros, np.gradient(speed, t), zeros+9.8))
    ts = np.arange(0., 8.5, SCAN_DT)
    straight_only = np.where(t < 3., speed, 0.)          # the front wall is only reliable in the straight
    front = 4.-np.interp(ts, t, np.cumsum(straight_only)*IMU_DT)+rng.normal(0., .002, ts.size)
    write(tmp_path/'scan.csv', ['t', 'front', 'front_min'], zip(ts, front, front))

    steps = {s['step']: s for s in analyse(str(tmp_path))['steps']}
    assert abs(steps['motor 20%']['velocidad_estable_mps']-top) < .03
    turn = steps['giro +20']
    assert abs(turn['angulo_con_vel_recta_deg']-angle) < 2.
    assert turn['signo_ok']


def _room_scan(x, y, th, n=306, fov=math.radians(110.), w=(-1.6, 1.4, -1.2, 1.3)):
    """Ranges of a LiDAR at (x, y, th) inside a rectangular room (x0, x1, y0, y1)."""
    x0, x1, y0, y1 = w
    angles = np.linspace(-fov, fov, n)
    out = []
    for a in angles:
        dx, dy = math.cos(th+a), math.sin(th+a)
        ts = [t for t in ((x0-x)/dx if dx < 0 else (x1-x)/dx if dx > 0 else math.inf,
                          (y0-y)/dy if dy < 0 else (y1-y)/dy if dy > 0 else math.inf) if t > 0]
        out.append(round(min(ts), 4))
    return float(angles[0]), float(angles[1]-angles[0]), out


def test_circle_gives_the_wheel_angle(tmp_path):
    import json
    angle, v, lidar_x = 20., .2, .06
    delta = math.radians(angle)
    # rear axle model: base_link 0.065 ahead of the rear axle
    commands = [(0., 'inicio', 'idle', 0., 1500, 0.), (1., 'ruedas a +20', 'circle_pre', angle, 1880, 0.)]
    t, dt = 2., .02
    for k in range(4):
        commands += [(t, f'circulo +20 pulso {k+1}', 'circle', angle, 1880, 20.),
                     (t+1., 'circulo +20 pausa', 'circle', angle, 1880, 0.)]
        t += 2.
    commands.append((t, 'centrar', 'circle_post', 0., 1500, 0.))
    write(tmp_path/'commands.csv', ['t', 'step', 'phase', 'servo_deg', 'servo_us', 'motor_pct'], commands)
    ts = np.arange(0., t+1., dt)
    moving = np.zeros(ts.size, bool)
    for k in range(4):
        moving |= (ts >= 2.+2*k) & (ts < 3.+2*k)
    speed = np.where(moving, v, 0.)
    yaw_rate = speed*math.tan(delta)/WHEELBASE
    rear = np.array([0., -.2]); th = 0.
    poses = []
    for s, r in zip(speed, yaw_rate):
        rear = rear+dt*s*np.array([math.cos(th), math.sin(th)])
        th += dt*r
        poses.append((rear[0]+.065*math.cos(th), rear[1]+.065*math.sin(th), th))
    zeros = np.zeros(ts.size)
    write(tmp_path/'imu.csv', ['t', 'gx', 'gy', 'gz', 'ax', 'ay', 'az'], zip(ts, zeros, zeros, yaw_rate, zeros, zeros, zeros+9.8))
    rows = []
    with open(tmp_path/'scans.jsonl', 'w') as f:
        for i in range(0, ts.size, 5):                      # 10 Hz
            x, y, h = poses[i]
            a0, inc, rr = _room_scan(x+lidar_x*math.cos(h), y+lidar_x*math.sin(h), h)
            f.write(json.dumps(dict(t=float(ts[i]), angle_min=a0, angle_increment=inc, range_min=.02, ranges=rr))+'\n')
            rows.append((ts[i], rr[len(rr)//2], rr[len(rr)//2]))
    write(tmp_path/'scan.csv', ['t', 'front', 'front_min'], rows)

    steps = {s['step']: s for s in analyse(str(tmp_path))['steps']}
    c = steps['circulo +20']
    assert abs(c['angulo_ruedas_deg']-angle) < 1.5, c
    assert c['signo_ok']
