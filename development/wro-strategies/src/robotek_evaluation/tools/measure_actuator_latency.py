#!/usr/bin/env python3
"""
Estimate steering actuator latency from a recorded run's telemetry.

Reads ``telemetry.csv`` (10 Hz), reconstructs the commanded steering angle from
``v_cmd``/``w_cmd`` with the bicycle model, and measures the lag between the
command and the actual front steering joint by normalized cross-correlation.
Also reports the achievable steer rate and the yaw-rate response lag.

  python3 src/robotek_evaluation/tools/measure_actuator_latency.py DIR [DIR ...]
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np

WHEELBASE = 0.1174  # must match open_config.py / the URDF


def load(path):
    rows = list(csv.DictReader((path / 'telemetry.csv').open()))

    def col(key):
        values = []
        for row in rows:
            try:
                values.append(float(row[key]))
            except (KeyError, ValueError):
                values.append(math.nan)
        return np.asarray(values)

    sim = col('sim_time')
    v = col('v_cmd')
    w = col('w_cmd')
    steer = col('steer_actual')
    gyro = col('gyro')
    with np.errstate(invalid='ignore', divide='ignore'):
        cmd = np.arctan(w * WHEELBASE / v)
    return sim, cmd, steer, gyro, v


def best_lag(reference, response, dt, max_lag, mask):
    """Return (lag_seconds, correlation) maximizing normalized correlation."""
    valid = mask & np.isfinite(reference) & np.isfinite(response)
    ref = reference[valid]
    res = response[valid]
    if ref.size < 20:
        return None, None
    ref = ref - ref.mean()
    res = res - res.mean()
    best = (0.0, -1.0)
    for k in range(-max_lag, max_lag + 1):
        if k < 0:
            a, b = ref[-k:], res[:k]
        elif k > 0:
            a, b = ref[:-k], res[k:]
        else:
            a, b = ref, res
        if a.size < 10:
            continue
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0.0:
            continue
        value = float(np.dot(a, b) / denom)
        if value > best[1]:
            best = (k * dt, value)
    return best


def measure(path):
    sim, cmd, steer, gyro, v = load(path)
    if sim.size < 20:
        return {'run': path.name, 'error': 'no telemetry'}
    dt = float(np.median(np.diff(sim))) if sim.size > 1 else 0.1
    active = (v > 0.1) & (np.abs(cmd) > 0.05)
    cmd_lag, cmd_corr = best_lag(cmd, steer, dt, 20, active)
    yaw_lag, yaw_corr = best_lag(cmd, gyro, dt, 20, active)
    rate = np.abs(np.diff(steer)) / np.maximum(np.diff(sim), 1e-6)
    return {
        'run': path.name,
        'samples': int(sim.size),
        'dt': round(dt, 4),
        'steer_cmd_lag_s': round(cmd_lag, 3) if cmd_lag is not None else None,
        'steer_cmd_corr': round(cmd_corr, 3) if cmd_corr is not None else None,
        'yaw_lag_s': round(yaw_lag, 3) if yaw_lag is not None else None,
        'yaw_corr': round(yaw_corr, 3) if yaw_corr is not None else None,
        'max_steer_rate_deg_s': round(float(np.nanmax(rate)) * 180.0 / math.pi, 1),
        'median_steer_deg': round(float(np.nanmedian(np.abs(steer[active]))) * 180.0 / math.pi, 1)
        if np.any(active) else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    results = [measure(path) for path in args.directories]
    for result in results:
        print(result)
    lags = [r['steer_cmd_lag_s'] for r in results if r.get('steer_cmd_lag_s') is not None]
    if lags:
        print(f'MEAN steer_cmd_lag_s {np.mean(lags):.3f} over {len(lags)} runs')


if __name__ == '__main__':
    main()
