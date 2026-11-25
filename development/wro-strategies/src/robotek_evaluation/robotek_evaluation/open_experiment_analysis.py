"""Offline Open telemetry merging and motion metrics; never a control input."""

import bisect
import csv
import json
import math
import shutil

from .open_field_geometry import inner_clearance


AUDIT_KEYS = ('x_gt', 'y_gt', 'yaw_gt', 'steer_actual', 'steer_right_actual', 'x_odom', 'y_odom')


def merge_audit_pose(directory, keys=AUDIT_KEYS):
    """Honest runs: fill the telemetry's ground-truth/steer columns from audit_pose.csv.

    The strategy never received these topics; the audit recorder did. Nearest sample
    in simulation time; the original strategy telemetry is kept as telemetry.raw.csv.
    """
    audit = directory / 'audit_pose.csv'
    telemetry = directory / 'telemetry.csv'
    if not audit.exists() or not telemetry.exists():
        return False
    with audit.open() as stream:
        poses = [r for r in csv.DictReader(stream)]
    if not poses:
        return False
    times = [float(r['sim_time']) for r in poses]
    with telemetry.open() as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    shutil.copyfile(telemetry, directory / 'telemetry.raw.csv')
    for row in rows:
        t = float(row['sim_time'])
        i = bisect.bisect_left(times, t)
        i = min(range(max(0, i - 1), min(len(poses), i + 1)), key=lambda k: abs(times[k] - t))
        for key in keys:
            if key in poses[i]:
                row[key] = poses[i][key]
    with telemetry.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return True


def summarize(directory):
    """Measure actual motion using ground truth and both clocks."""
    path = directory / 'telemetry.csv'
    if not path.exists():
        return {'completed': False, 'reason': 'No telemetry received'}
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    moving = next((i for i, r in enumerate(rows) if float(r['v_cmd']) > 0), None)
    done = next((i for i, r in enumerate(rows) if r['state'] == 'DONE'), None)
    result = {'completed': done is not None, 'samples': len(rows)}
    if moving is None:
        return result
    end = done if done is not None else len(rows) - 1
    rows = rows[moving:end + 1]
    if 'selected_direction' in rows[-1]:
        result['selected_direction'] = rows[-1]['selected_direction']
        result['direction_reason'] = rows[-1]['direction_reason']
        expected = json.loads((directory / 'manifest.json').read_text())['direction']
        result['direction_matches_test_orientation'] = result['selected_direction'] == expected
    for clock in ('wall_time', 'sim_time'):
        result[clock + '_seconds'] = float(rows[-1][clock]) - float(rows[0][clock])
    result['state_wall_seconds'] = {}
    for a, b in zip(rows, rows[1:]):
        delta = float(b['wall_time']) - float(a['wall_time'])
        state = a['state']
        result['state_wall_seconds'][state] = result['state_wall_seconds'].get(state, 0) + delta
    result['turn_timeouts'] = int(rows[-1]['turn_timeouts'])
    result['recovery_entries'] = sum(
        a['state'] != 'RECOVER' and b['state'] == 'RECOVER'
        for a, b in zip(rows, rows[1:])
    )
    result['turns'] = int(rows[-1]['turns'])
    result['lap_markers'] = []
    previous = float(rows[0]['wall_time'])
    for lap in (1, 2, 3):
        marker = next((r for r in rows if int(r['turns']) >= 4 * lap), None)
        if marker:
            timestamp = float(marker['wall_time'])
            result['lap_markers'].append({
                'lap': lap, 'wall_seconds': timestamp - previous,
                'cumulative_wall_seconds': timestamp - float(rows[0]['wall_time']),
            })
            previous = timestamp
    poses = [
        (float(r['x_gt']), float(r['y_gt']), float(r['yaw_gt']))
        for r in rows if math.isfinite(float(r['x_gt']))
    ]
    if poses:
        manifest = json.loads((directory / 'manifest.json').read_text())
        geometry = manifest.get('field_geometry', {
            'inner': {'xmin': -0.5, 'xmax': 0.5, 'ymin': -0.5, 'ymax': 0.5},
            'outer': {'xmin': -1.5, 'xmax': 1.5, 'ymin': -1.5, 'ymax': 1.5},
            'island': {'center_x': 0.0, 'center_y': 0.0},
        })
        inner, outer = geometry['inner'], geometry['outer']
        result['gt_path_m'] = sum(
            math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(poses, poses[1:])
        )
        bearings = [
            math.atan2(y - geometry['island']['center_y'], x - geometry['island']['center_x'])
            for x, y, yaw in poses
        ]
        winding = sum(
            math.atan2(math.sin(b - a), math.cos(b - a))
            for a, b in zip(bearings, bearings[1:])
        )
        result['gt_winding_laps'] = abs(winding) / (2 * math.pi)
        result['final_gt_pose'] = poses[-1]
        result['min_outer_body_clearance_m'] = min(
            min(
                min(x - outer['xmin'], outer['xmax'] - x)
                - (0.089 * abs(math.cos(yaw)) + 0.05 * abs(math.sin(yaw))),
                min(y - outer['ymin'], outer['ymax'] - y)
                - (0.089 * abs(math.sin(yaw)) + 0.05 * abs(math.cos(yaw))),
            ) for x, y, yaw in poses
        )
        # Conservative bounding-circle margin around the actual island.
        result['min_inner_body_clearance_m'] = min(
            inner_clearance(x, y, inner)
            for x, y, yaw in poses
        )
    errors = [
        abs(float(r['heading_error'])) for r in rows
        if r['state'] == 'FOLLOW' and math.isfinite(float(r['corner_distance']))
        and float(r['corner_distance']) > 0.3
    ]
    result['straight_heading_error_mean_rad'] = sum(errors) / len(errors) if errors else None
    manifest = json.loads((directory / 'manifest.json').read_text())
    config = manifest['resolved_config']
    actual = [
        abs(float(r[key])) for r in rows for key in ('steer_actual', 'steer_right_actual')
        if r.get(key)
    ]
    commanded = [
        abs(math.atan(float(r['w_cmd']) * config['wheelbase'] / float(r['v_cmd'])))
        for r in rows if abs(float(r['v_cmd'])) > 1e-6
    ]
    result['max_actual_steer_deg'] = math.degrees(max(actual)) if actual else None
    result['max_command_steer_deg'] = math.degrees(max(commanded)) if commanded else None
    result['command_saturation_fraction'] = (
        sum(s >= 0.98 * config['steer_limit'] for s in commanded) / len(commanded)
        if commanded else None
    )
    result['min_front_range_m'] = min(float(r['front']) for r in rows)
    if poses:
        x, y, yaw = poses[-1]
        half_x = 0.089 * abs(math.cos(yaw)) + 0.05 * abs(math.sin(yaw))
        half_y = 0.089 * abs(math.sin(yaw)) + 0.05 * abs(math.cos(yaw))
        result['finish_body_in_start_section'] = (
            abs(x) + half_x < 0.5 and y - half_y > -1.5 and y + half_y < -0.5
        )
        result['validated_completed'] = bool(
            result['completed'] and result['turns'] == 4 * config['laps']
            and result['gt_winding_laps'] > config['laps'] - 0.12
            and result['finish_body_in_start_section']
            and result['min_outer_body_clearance_m'] > 0.05
            and result['min_inner_body_clearance_m'] > 0.05
            and result['recovery_entries'] == 0 and result['turn_timeouts'] == 0
            and result['max_actual_steer_deg'] <= math.degrees(config['steer_limit']) + 0.05
            and result['max_command_steer_deg'] <= math.degrees(config['steer_limit']) + 0.05
            and result.get('direction_matches_test_orientation', True)
        )
    result['turn_events'] = []
    entry = None
    for index, row in enumerate(rows):
        if row['state'] == 'TURN' and (index == 0 or rows[index - 1]['state'] != 'TURN'):
            entry = row
        if entry and row['state'] in ('FOLLOW', 'FINISH'):
            result['turn_events'].append({
                'turn': int(row['turns']),
                'wall_seconds': float(row['wall_time']) - float(entry['wall_time']),
                'sim_seconds': float(row['sim_time']) - float(entry['sim_time']),
                'entry_gt': [float(entry[k]) for k in ('x_gt', 'y_gt', 'yaw_gt')],
                'exit_gt': [float(row[k]) for k in ('x_gt', 'y_gt', 'yaw_gt')],
                'exit_heading_error_rad': float(row['heading_error']),
                'exit_actual_steer_deg': math.degrees(float(row['steer_actual'])),
            })
            entry = None
    return result
