"""Analysis of the actuator step tests (no ROS): servo and motor response times and angles.

Input: the three CSV files written by actuator_test in one run directory
  commands.csv  t, step, phase, servo_deg, servo_us, motor_pct
  imu.csv       t, gx, gy, gz, ax, ay, az        (rad/s, m/s^2, as received)
  scan.csv      t, front, front_min              (m; front = median ±10 deg ahead)
All times are the receiving node's clock, so delays include the ROS transport (~ms).

Per step (one row of commands.csv with a changed command):
  - servo on the bench (car still): onset of chassis vibration in the IMU. Only an
    approximate servo delay; the wheel angle cannot be seen without moving.
  - motor (pulses of at most 0.25 s, so the speed never settles): delay to the first
    acceleration (IMU forward axis, FORWARD_AXIS) and to the first LiDAR motion, peak speed two ways (IMU x
    acceleration integrated from the pulse start; LiDAR front distance, which at 10 Hz
    smooths and underestimates such a short peak), stopping time and total distance.
  - steering: wheels already turned, then a motor pulse; the effective wheel angle
    atan(r * wheelbase / v) while the car rolls, with v from the LiDAR at the same instants
    (median over the samples with v > 0.1 m/s), and the angle from the turned heading over
    the travelled distance (yaw change = distance * tan(angle) / wheelbase), which averages
    out the vibration. The servo delay comes from the bench test.
  - long pulses (>= LONG_PULSE s, low power): steady speed of a straight pulse (LiDAR, last
    40 % of the pulse) and steady yaw rate of a turn (median gyro z, last half of the pulse);
    a turn with the same motor % as a straight pulse of the run gets
    angulo_con_vel_recta = atan(steady yaw rate * wheelbase / straight steady speed).
  - circle (wheels fixed, several pulses): arc length from the LiDAR odometry
    (robotek_common.lidar_odometry, scans.jsonl) and yaw from the gyro; radius of base_link
    = length / yaw, rear-axle radius = sqrt(R^2 - BASE_FROM_REAR^2), wheel angle =
    atan(wheelbase / rear-axle radius). Speed-free, so the most direct measure.

  ros2 run robotek_hardware actuator_report <run_dir>   # re-analyse a saved run
"""
import csv
import json
import math
import os
import sys

import numpy as np

WHEELBASE = .11883       # m, robotek_common/vehicle.py and robot.yaml
# The RRC Lite board sits turned 90 deg about the vertical: the car's forward axis is the
# board's +y (measured 8 oct 2026: integrating ay matches the LiDAR distance; ax stays ~0).
# Gyro z (yaw) is unaffected.
FORWARD_AXIS = 'ay'   # old flat build; measure again for the vertical board (imu_axes)
SPEED_WINDOW = .3        # s of LiDAR samples per speed estimate (10 Hz scan: 3-4 samples)
LONG_PULSE = .6          # s: from here on a pulse is long enough to reach a steady state
BASE_FROM_REAR = .059415 # m, base_link ahead of the rear axle (vehicle.py REAR_AXLE_X)


def read_csv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}
    out = {}
    for key in rows[0]:
        try:
            out[key] = np.array([float(r[key]) for r in rows])
        except ValueError:
            out[key] = np.array([r[key] for r in rows])
    return out


def baseline(t, y, t0, window=.3):
    """Mean and spread of y just before t0."""
    m = (t >= t0-window) & (t < t0)
    if m.sum() < 3:
        m = t < t0
    if m.sum() == 0:
        return float(y[0]), 0.
    return float(np.mean(y[m])), float(np.std(y[m]))


def onset(t, y, t0, t_end, k=4., min_delta=0., hold=2, window=.3):
    """Delay from t0 until y leaves the pre-step noise band `hold` samples in a row."""
    mean, sd = baseline(t, y, t0, window)
    threshold = max(k*sd, min_delta)
    m = (t >= t0) & (t <= t_end)
    times, outside = t[m], np.abs(y[m]-mean) > threshold
    run = 0
    for i, flag in enumerate(outside):
        run = run+1 if flag else 0
        if run >= hold:
            return float(times[i-hold+1]-t0)
    return None


def step_response(t, y, t0, t_end, tail=.3, **onset_args):
    """Delay, 63 % time and final value of a step that starts at t0 and lasts until t_end."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    start, _ = baseline(t, y, t0)
    m = (t >= t0) & (t <= t_end)
    times, values = t[m], y[m]
    if times.size < 4:
        return None
    final = float(np.median(values[times >= t_end-(t_end-t0)*tail]))
    change = final-start
    delay = onset(t, y, t0, t_end, **onset_args)
    t63 = None
    if change != 0.:
        crossed = np.nonzero((values-start)/change >= .63)[0]
        if crossed.size:
            t63 = float(times[crossed[0]]-t0)
    tau = None if t63 is None or delay is None else max(0., t63-delay)
    return dict(start=start, final=final, change=change, delay=delay, t63=t63, tau=tau)


def speeds(t, front, window=SPEED_WINDOW):
    """Forward speed from the front distance: minus the slope of a sliding linear fit."""
    t, front = np.asarray(t, float), np.asarray(front, float)
    out = np.full(t.size, np.nan)
    for i in range(t.size):
        m = (np.abs(t-t[i]) <= window/2) & np.isfinite(front)
        if m.sum() >= 3:
            out[i] = -np.polyfit(t[m], front[m], 1)[0]
    return out


def _round(value, digits=3):
    return None if value is None or not math.isfinite(value) else round(float(value), digits)


def steps_of(commands):
    """Command changes: (index, t0, t_next, row) for each step of the plan."""
    t = commands['t']
    keys = ('servo_deg', 'motor_pct')
    out = []
    for i in range(t.size):
        if i and all(commands[k][i] == commands[k][i-1] for k in keys) \
                and commands['step'][i] == commands['step'][i-1]:
            continue
        out.append(i)
    result = []
    for n, i in enumerate(out):
        t_next = t[out[n+1]] if n+1 < len(out) else t[-1]
        result.append((i, float(t[i]), float(t_next)))
    return result


def analyse_servo_bench(commands, imu, i, t0, t1):
    gyro = np.linalg.norm(np.stack([imu['gx'], imu['gy'], imu['gz']]), axis=0)
    accel_y = imu['ay']
    return dict(
        kind='servo_banco', servo_deg=float(commands['servo_deg'][i]),
        servo_us=float(commands['servo_us'][i]),
        delay_vibracion_gyro_s=_round(onset(imu['t'], gyro, t0, t1, k=5., min_delta=.02)),
        delay_vibracion_acc_y_s=_round(onset(imu['t'], accel_y, t0, t1, k=5., min_delta=.15)),
        nota='aproximado: vibracion del chasis, no el angulo de las ruedas')


def analyse_motor(commands, imu, scan, i, t0, t1, t_end, kind_hold=False):
    """Motor pulse from t0 to t1 (motor back to 0), coasting until t_end."""
    pct = float(commands['motor_pct'][i])
    out = dict(kind='motor', motor_pct=pct, pulso_s=_round(t1-t0))
    out['delay_aceleracion_s'] = _round(onset(imu['t'], imu[FORWARD_AXIS], t0, t1+.2, k=4., min_delta=.3))
    st, front = scan['t'], scan['front']
    moved = None
    start, _ = baseline(st, front, t0, window=.5)
    m = (st >= t0) & (st <= t_end)
    for tt, d in zip(st[m], front[m]):
        if math.isfinite(d) and start-d > .02:
            moved = tt-t0
            break
    out['delay_movimiento_lidar_s'] = _round(moved)
    it = imu['t']
    rest, _ = baseline(it, imu[FORWARD_AXIS], t0)
    pulse = (it >= t0) & (it <= t1+.3)
    if pulse.sum() >= 2:
        integrated = np.cumsum((imu[FORWARD_AXIS][pulse]-rest)*np.gradient(it[pulse]))
        out['velocidad_max_imu_mps'] = _round(float(integrated.max()))
    v = speeds(st, front)
    window = (st >= t0) & (st <= t_end)
    peak = float(np.nanmax(v[window])) if np.isfinite(v[window]).any() else None
    out['velocidad_max_lidar_mps'] = _round(peak)
    if t1-t0 >= LONG_PULSE or kind_hold:
        # after a ramp step the speed is already there: use most of the hold
        tail = (st >= t1-(.7 if kind_hold else .4)*(t1-t0)) & (st <= t1) & np.isfinite(v)
        out['velocidad_estable_mps'] = _round(float(np.median(v[tail]))) if tail.any() else None
    out['se_mueve'] = bool(moved is not None and peak is not None and peak > .05)
    if out['se_mueve']:
        top = np.nonzero(window & (v >= peak))[0]
        stopped = np.nonzero(window & (st > st[top[0]]) & (v < .05))[0] if top.size else []
        out['tiempo_hasta_parar_s'] = _round(st[stopped[0]]-t1) if len(stopped) else None
        ok = window & np.isfinite(front)
        out['distancia_total_m'] = _round(start-front[ok][-1]) if ok.any() else None
    # Wheelie check (board turned 90 deg: pitch = gyro x).
    m = (it >= t0) & (it <= min(t_end, t1+.6))
    if m.any():
        out['cabeceo_max_rad_s'] = _round(float(np.abs(imu['gx'][m]).max()))
        out['az_min_m_s2'] = _round(float(imu['az'][m].min()), 1)
    return out


def analyse_steer(commands, imu, scan, i, t0, t_end, t_off=None, straight_speed=None):
    """Wheels already at the angle; motor pulse from t0 to t_off, the car rolls until t_end."""
    deg = float(commands['servo_deg'][i])
    out = dict(kind='giro', servo_deg=deg, motor_pct=float(commands['motor_pct'][i]))
    it, gz = imu['t'], imu['gz']
    m = (it >= t0) & (it <= t_end)
    if m.sum() < 3:
        return dict(out, error='sin datos de IMU')
    bias, _ = baseline(it, gz, t0, window=.5)
    if t_off is not None and t_off-t0 >= LONG_PULSE:
        steady = (it >= t0+.5*(t_off-t0)) & (it <= t_off)
        if steady.sum() >= 3:
            rate = float(np.median(gz[steady]-bias))
            out['yaw_rate_estable_rad_s'] = _round(rate)
            if straight_speed and straight_speed > .05:
                out['velocidad_recta_mps'] = _round(straight_speed)
                out['angulo_con_vel_recta_deg'] = _round(
                    math.degrees(math.atan(rate*WHEELBASE/straight_speed)), 1)
    yaw = float(np.sum((gz[m]-bias)*np.gradient(it[m])))
    out['giro_total_deg'] = _round(math.degrees(yaw), 1)
    st, front = scan['t'], scan['front']
    start, _ = baseline(st, front, t0, window=.5)
    after = (st >= t_end-.3) & (st <= t_end) & np.isfinite(front)
    distance = start-float(np.median(front[after])) if after.any() else None
    out['distancia_m'] = _round(distance)
    if distance and distance > .02:
        # Over a short arc the LiDAR front distance is ~ the travelled distance.
        out['angulo_por_rumbo_deg'] = _round(math.degrees(math.atan(yaw*WHEELBASE/distance)), 1)
    v = speeds(st, front)
    ok = np.isfinite(v)
    if ok.sum() >= 2:
        v_at = np.interp(it, st[ok], v[ok])
        out['velocidad_max_mps'] = _round(float(np.max(v_at[m])))
        use = m & (v_at > .1)
        if use.sum() >= 3:
            angles = np.degrees(np.arctan((gz[use]-bias)*WHEELBASE/v_at[use]))
            out['angulo_instantaneo_deg'] = _round(float(np.median(angles)), 1)
    best = out.get('angulo_con_vel_recta_deg', out.get('angulo_por_rumbo_deg'))
    out['signo_ok'] = None if best is None else bool(deg == 0. or np.sign(best) == np.sign(deg))
    if best is None:
        out['nota'] = 'el coche no avanzo lo suficiente (> 2 cm)'
    return out


class _Scan:
    def __init__(self, d):
        self.angle_min, self.angle_increment = d['angle_min'], d['angle_increment']
        self.range_min = d.get('range_min', 0.)
        self.ranges = [math.inf if r is None else r for r in d['ranges']]


def analyse_circle(run_dir, commands, imu, side, t0, t_end):
    """Arc driven with the wheels at `side` deg between t0 and t_end (pulses and pauses)."""
    from robotek_common.lidar_odometry import LidarOdometry
    path = os.path.join(run_dir, 'scans.jsonl')
    if not os.path.exists(path):
        return dict(kind='circulo', servo_deg=side, error='sin scans.jsonl')
    it, gz = imu['t'], imu['gz']
    bias, _ = baseline(it, gz, t0, window=.8)
    yaw_at = lambda t: float(np.sum((gz[(it >= t0) & (it <= t)]-bias)*np.gradient(it)[(it >= t0) & (it <= t)]))
    odo, length, scans, matched = LidarOdometry(), 0., 0, 0
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            if not t0-.3 <= d['t'] <= t_end:
                continue
            odo.scan(_Scan(d), yaw_at(d['t']))
            if d['t'] >= t0:
                scans += 1
                matched += odo.last_quality == 'lidar'
                length += odo.read()
            else:
                odo.read()
    yaw = yaw_at(t_end)
    out = dict(kind='circulo', servo_deg=side, arco_m=_round(length), giro_deg=_round(math.degrees(yaw), 1),
               scans_alineados=f'{matched}/{scans}')
    if abs(yaw) > math.radians(5.) and length > .1:
        radius = length/abs(yaw)
        rear = math.sqrt(max(radius**2-BASE_FROM_REAR**2, 1e-6))
        angle = math.degrees(math.atan(WHEELBASE/rear))*math.copysign(1., yaw)
        out.update(radio_m=_round(radius), angulo_ruedas_deg=_round(angle, 1),
                   signo_ok=bool(np.sign(angle) == np.sign(side)))
    else:
        out['nota'] = 'arco o giro demasiado pequenos'
    return out


def analyse(run_dir):
    commands = read_csv(os.path.join(run_dir, 'commands.csv'))
    imu = read_csv(os.path.join(run_dir, 'imu.csv'))
    scan = read_csv(os.path.join(run_dir, 'scan.csv'))
    results = []
    if not commands or not imu:
        return dict(run_dir=run_dir, error='faltan commands.csv o imu.csv', steps=[])
    steps = steps_of(commands)
    phase = [str(commands['phase'][i]) for i, _, _ in steps]
    label = [str(commands['step'][i]) for i, _, _ in steps]

    def end_of(n, phases):
        """End of the run of consecutive steps from n whose phase is in phases."""
        while n+1 < len(steps) and phase[n+1] in phases:
            n += 1
        return steps[n][2]

    straight = {}   # motor % -> steady speed of a straight long pulse in this run
    done_circles = set()
    for n, (i, t0, t1) in enumerate(steps):
        if label[n].startswith('corte'):
            continue
        if phase[n] == 'circle' and float(commands['servo_deg'][i]) not in done_circles:
            side = float(commands['servo_deg'][i])
            done_circles.add(side)
            last = n
            while last+1 < len(steps) and phase[last+1] == 'circle':
                last += 1
            results.append(dict(analyse_circle(run_dir, commands, imu, side, t0, steps[last][2]),
                                step=f'circulo {side:+.0f}'))
            continue
        row = None
        if phase[n] == 'servo':
            row = analyse_servo_bench(commands, imu, i, t0, t1)
        elif phase[n] == 'motor' and commands['motor_pct'][i] != 0. and scan:
            stop = next((k for k in range(n+1, len(steps)) if commands['motor_pct'][steps[k][0]] == 0.), None)
            if stop is None:
                off, t_end = t1, t1
            else:
                # the coast lasts over every following step with the motor at 0 (cut row included)
                last = stop
                while last+1 < len(steps) and commands['motor_pct'][steps[last+1][0]] == 0. \
                        and phase[last+1] == 'motor':
                    last += 1
                off, t_end = steps[stop][1], steps[last][2]
            row = analyse_motor(commands, imu, scan, i, t0, off, t_end,
                                kind_hold=n > 0 and phase[n-1] == 'ramp')
            if row.get('velocidad_estable_mps'):
                straight[float(commands['motor_pct'][i])] = row['velocidad_estable_mps']
        elif phase[n] == 'turn' and scan:
            off = next((steps[k][1] for k in range(n+1, len(steps))
                        if commands['motor_pct'][steps[k][0]] == 0.), t1)
            row = analyse_steer(commands, imu, scan, i, t0, end_of(n, ('turn', 'turn_coast')),
                                off, straight.get(float(commands['motor_pct'][i])))
        if row is not None:
            results.append(dict(row, step=label[n]))
    return dict(run_dir=run_dir, wheelbase_m=WHEELBASE, steps=results)


def write_summary(run_dir):
    summary = analyse(run_dir)
    with open(os.path.join(run_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print('uso: actuator_report <run_dir>')
        return 2
    summary = write_summary(argv[0])
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
