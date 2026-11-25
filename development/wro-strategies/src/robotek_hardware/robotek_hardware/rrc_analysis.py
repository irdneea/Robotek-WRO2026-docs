"""Verdicts for the RRC Lite board test (no ROS): rates, IMU at rest, battery, button.

Input of each function is plain lists collected by rrc_test. Statuses: PASS, WARN, FAIL,
INFO (measured, nothing to compare with) and MANUAL (the car cannot check it: the person
looks or listens). The limits are for the real car at rest (docs/ros-robot-controller-oficial.md).
"""
import math

GRAVITY = 9.80665
IMU_MIN_HZ = 40.        # measured ~49 Hz on the car (7 oct 2026)
ACCEL_NORM_TOL = 1.0    # m/s^2 around g with the car still
GYRO_MEAN_MAX = 0.03    # rad/s (~1.7 deg/s): bigger = moving or a large bias
BATTERY_MIN_V = 5.5     # 2S pack: 6.0 empty .. 8.4 full; outside this the reading is wrong
BATTERY_MAX_V = 9.0


def stats(values):
    n = len(values)
    if not n:
        return dict(n=0, mean=None, std=None, min=None, max=None)
    mean = sum(values)/n
    std = math.sqrt(sum((v-mean)**2 for v in values)/n)
    return dict(n=n, mean=mean, std=std, min=min(values), max=max(values))


def rate_hz(stamps):
    """Messages per second from receive times (s); None with fewer than 2 samples."""
    if len(stamps) < 2 or stamps[-1] <= stamps[0]:
        return None
    return (len(stamps)-1)/(stamps[-1]-stamps[0])


def imu_report(samples):
    """samples: (t, ax, ay, az, gx, gy, gz, orientation_is_zero), SI units as published."""
    if not samples:
        return 'FAIL', {'motivo': 'sin mensajes de imu_raw (¿recepcion de la placa activada?)'}
    t = [s[0] for s in samples]
    accel = [math.sqrt(s[1]**2+s[2]**2+s[3]**2) for s in samples]
    gyro = [stats([s[4+i] for s in samples]) for i in range(3)]
    detail = dict(muestras=len(samples), hz=rate_hz(t), aceleracion_norma=stats(accel),
                  giro_x=gyro[0], giro_y=gyro[1], giro_z=gyro[2],
                  orientacion_vacia=all(s[7] for s in samples))
    problems = []
    if detail['hz'] is None or detail['hz'] < IMU_MIN_HZ:
        problems.append(f'frecuencia {detail["hz"]} Hz < {IMU_MIN_HZ}')
    if abs(detail['aceleracion_norma']['mean']-GRAVITY) > ACCEL_NORM_TOL:
        problems.append('la norma de la aceleracion no es g (¿unidades o coche en movimiento?)')
    big = [axis for axis, g in zip('xyz', gyro) if abs(g['mean']) > GYRO_MEAN_MAX]
    if big:
        problems.append(f'giroscopio con media alta en {",".join(big)}: coche en movimiento o sesgo grande')
    detail['problemas'] = problems
    if detail['hz'] is None or detail['hz'] < IMU_MIN_HZ or not detail['aceleracion_norma']['n']:
        return 'FAIL', detail
    return ('WARN' if problems else 'PASS'), detail


def battery_report(samples):
    """samples: (t, volts)."""
    if not samples:
        return 'FAIL', {'motivo': 'sin mensajes de battery'}
    volts = [v for _, v in samples]
    detail = dict(muestras=len(volts), hz=rate_hz([t for t, _ in samples]), voltios=stats(volts))
    if min(volts) < BATTERY_MIN_V or max(volts) > BATTERY_MAX_V:
        detail['motivo'] = f'fuera de {BATTERY_MIN_V}-{BATTERY_MAX_V} V: lectura o unidades incorrectas'
        return 'FAIL', detail
    return 'PASS', detail


def button_report(events):
    """events: (t, id, state). PASS when at least one press arrives; lists the states seen."""
    seen = sorted({(i, s) for _, i, s in events})
    detail = dict(eventos=len(events), ids_estados=[list(x) for x in seen])
    if not events:
        return 'FAIL', {**detail, 'motivo': 'ningun evento: ¿se pulso? ¿la recepcion esta activada?'}
    return 'PASS', detail


def topic_report(publishers, subscribers, expected_pubs, expected_subs):
    """publishers/subscribers: {topic: count}. Lists what is missing."""
    missing_pubs = [t for t in expected_pubs if not publishers.get(t)]
    missing_subs = [t for t in expected_subs if not subscribers.get(t)]
    detail = dict(sin_publicador=missing_pubs, sin_suscriptor=missing_subs)
    return ('PASS' if not (missing_pubs or missing_subs) else 'FAIL'), detail
