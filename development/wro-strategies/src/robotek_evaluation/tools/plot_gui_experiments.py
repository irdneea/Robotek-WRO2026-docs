#!/usr/bin/env python3
"""Plot recorded vehicle trajectories, steering and lidar for GUI experiments."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np


def field(axis, geometry=None):
    """Draw the wall bounds recorded for this experiment."""
    geometry = geometry or {
        'outer': {'xmin': -1.5, 'xmax': 1.5, 'ymin': -1.5, 'ymax': 1.5},
        'inner': {'xmin': -0.5, 'xmax': 0.5, 'ymin': -0.5, 'ymax': 0.5},
    }
    for key in ('outer', 'inner'):
        bounds = geometry[key]
        axis.add_patch(Rectangle(
            (bounds['xmin'], bounds['ymin']), bounds['xmax'] - bounds['xmin'],
            bounds['ymax'] - bounds['ymin'], fill=key == 'inner', color='black',
            alpha=0.15 if key == 'inner' else 1.0))
    axis.set(xlim=(-1.6, 1.6), ylim=(-1.6, 1.6), xlabel='x (m)', ylabel='y (m)')
    axis.set_aspect('equal')
    axis.grid(alpha=0.2)


def main():
    matplotlib.use('Agg')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    parser.add_argument('--comparison', type=Path)
    args = parser.parse_args()
    comparison, comparison_axis = plt.subplots(figsize=(7, 7))
    reference = json.loads((args.directories[0] / 'manifest.json').read_text()).get(
        'field_geometry')
    field(comparison_axis, reference)
    for directory in args.directories:
        geometry = json.loads((directory / 'manifest.json').read_text()).get('field_geometry')
        if args.comparison and geometry != reference:
            raise ValueError('Compare trajectories with the same field geometry per image')
        with (directory / 'telemetry.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        first = next(i for i, r in enumerate(rows) if float(r['v_cmd']) > 0)
        last = next((i for i, r in enumerate(rows) if r['state'] == 'DONE'), len(rows) - 1)
        rows = rows[first:last + 1]

        def values(key):
            return np.array([float(r[key]) if r[key] else np.nan for r in rows])

        t = values('wall_time') - float(rows[0]['wall_time'])
        x, y = values('x_gt'), values('y_gt')
        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        name = directory.name.split('Z-', 1)[-1]
        fig.suptitle(name)
        field(axes[0, 0], geometry)
        axes[0, 0].plot(x, y, linewidth=1.4, label='Ground truth')
        transitions = [
            i for i in range(1, len(rows))
            if rows[i]['state'] == 'TURN' and rows[i - 1]['state'] != 'TURN'
        ]
        axes[0, 0].scatter(x[transitions], y[transitions], s=20, label='Turn entry')
        axes[0, 0].scatter(x[-1], y[-1], marker='x', s=70, label='Stop / last pose')
        axes[0, 0].legend(fontsize=8)
        comparison_axis.plot(x, y, linewidth=1, alpha=0.8, label=name)
        axes[0, 1].plot(t, values('heading_error'), label='Heading error (rad)')
        axes[0, 1].plot(t, values('gyro'), label='IMU yaw rate (rad/s)', alpha=0.6)
        axes[0, 1].set(ylabel='rad / rad/s', xlabel='Wall time since motion (s)')
        axes[0, 1].legend(fontsize=8)
        axes[1, 0].plot(t, values('steer_actual'), label='Left steering (rad)')
        if 'steer_right_actual' in rows[0]:
            axes[1, 0].plot(t, values('steer_right_actual'),
                            label='Right steering (rad)', alpha=0.6)
        v, w = values('v_cmd'), values('w_cmd')
        steering = np.arctan(np.divide(w * 0.13, v, out=np.zeros_like(v), where=v != 0))
        axes[1, 0].plot(t, steering, label='Commanded steering (rad)', alpha=0.6)
        axes[1, 0].set(ylabel='Steering (rad)', xlabel='Wall time since motion (s)')
        axes[1, 0].legend(fontsize=8)
        for key in ('left', 'right', 'front', 'corner_distance'):
            data = values(key)
            data[~np.isfinite(data)] = np.nan
            axes[1, 1].plot(t, data, label=key, alpha=0.8)
        axes[1, 1].set(ylim=(0, 2.7), ylabel='LiDAR distance (m)',
                       xlabel='Wall time since motion (s)')
        axes[1, 1].legend(fontsize=8)
        for axis in axes.flat:
            axis.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(directory / 'telemetry.png', dpi=160)
        plt.close(fig)
    comparison_axis.legend(fontsize=8)
    comparison_axis.set_title('GUI experiments: measured ground-truth trajectories')
    comparison.tight_layout()
    if args.comparison:
        comparison.savefig(args.comparison, dpi=160)
    plt.close(comparison)


if __name__ == '__main__':
    main()
