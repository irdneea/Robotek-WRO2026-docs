"""Judge a parking-only round from ground truth (rules 1.8, Appendix A section 6).

- Fully parked: the robot's projection (chassis and wheels) is completely inside the
  lot rectangle and the robot is parallel to the wall: the two wheels on the wall side
  differ by at most 20 mm in their distance to the wall. -> 15 points
- Partly parked (projection only partly inside) or not parallel. -> 7 points
- Touching a parking lot limit stops the robot: no parking points.
Estimated points; the start-from-the-lot bonus (1.8.1) is not evaluated here.
"""
import csv
import json
import math

from . import contact_log
from .obstacle_audit_geometry import collision_polygons, polygon_distance, rectangle

PARALLEL_TOLERANCE = .02  # m
SETTLE = 1.               # s after the stop before measuring


def _events(directory):
    path = directory/'events.jsonl'
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _contacts(directory):
    path = directory/'contacts.jsonl'
    if not path.exists():
        return []
    return contact_log.read(path)


def summarize_parking(directory, manifest):
    lot = manifest['parking_lot']
    events = _events(directory)
    start = next((e for e in events if e.get('event') == 'start'), None)
    done = next((e for e in events if e.get('event') == 'done'), None)
    plans = [e for e in events if e.get('event') == 'park_plan']
    rows = []
    path = directory/'telemetry.csv'
    if path.exists():
        with path.open() as stream:
            rows = [r for r in csv.DictReader(stream)
                    if all(r.get(k) not in (None, '', 'nan') for k in ('x_gt', 'y_gt', 'yaw_gt', 'steer_actual'))]
    touched = [c for c in _contacts(directory) if c.get('kind') == 'parking_limit']
    walls = [c for c in _contacts(directory) if c.get('kind') in ('outer_wall', 'inner_wall')]
    limits = [rectangle(lot['x0']-.01, (lot['y0']+lot['y1'])/2, 0., .01, .10),
              rectangle(lot['x1']+.01, (lot['y0']+lot['y1'])/2, 0., .01, .10)]
    min_limit = min((polygon_distance(shape, box) for r in rows for shape in collision_polygons(r).values()
                     for box in limits), default=None)
    report = dict(test_scope='parking_only', name=manifest.get('name'), direction=manifest['direction'],
                  official_points=None, parking_lot=lot, completed=done is not None,
                  parking_plans=len(plans), limit_touched=bool(touched), wall_contacts=contact_log.message_count(walls),
                  min_limit_clearance_m=min_limit,
                  max_steer_degrees=max((abs(math.degrees(float(r[k]))) for r in rows
                                         for k in ('steer_actual', 'steer_right_actual')), default=None),
                  timings=None, points_estimated=0, verdict='not_parked')
    if start and done:
        report['timings'] = {k+'_seconds': done[k]-start[k] for k in ('sim_time', 'wall_time')}
    final = [r for r in rows if done and float(r['sim_time']) >= done['sim_time']+SETTLE] or rows[-1:]
    if not final:
        report['verdict'] = 'no_ground_truth'
        return report
    r = final[-1]
    shapes = collision_polygons(r)
    vertices = [p for shape in shapes.values() for p in shape]

    def inside(p):
        return lot['x0'] <= p[0] <= lot['x1'] and lot['y0'] <= p[1] <= lot['y1']
    fully = all(inside(p) for p in vertices)
    partly = any(inside(p) for p in vertices)
    # Wall-side wheels: the side whose wheels are closer to the outer wall (y = y0).
    side = min(('left', 'right'), key=lambda s: sum(
        sum(p[1] for p in shapes[f'{a}_{s}_wheel']) for a in ('front', 'rear')))
    distance = {a: min(p[1] for p in shapes[f'{a}_{side}_wheel'])-lot['y0'] for a in ('front', 'rear')}
    parallel = abs(distance['front']-distance['rear']) <= PARALLEL_TOLERANCE
    report.update(final_pose=dict(x=float(r['x_gt']), y=float(r['y_gt']),
                                  yaw_deg=math.degrees(float(r['yaw_gt']))),
                  fully_inside=fully, partly_inside=partly and not fully, parallel=parallel,
                  wall_side_wheel_to_wall_m=distance,
                  wheel_distance_difference_m=abs(distance['front']-distance['rear']),
                  margins_m=dict(x0=min(p[0] for p in vertices)-lot['x0'], x1=lot['x1']-max(p[0] for p in vertices),
                                 wall=min(p[1] for p in vertices)-lot['y0'],
                                 lot_line=lot['y1']-max(p[1] for p in vertices)))
    if touched:
        report.update(points_estimated=0, verdict='limit_touched')
    elif fully and parallel:
        report.update(points_estimated=15, verdict='parked_fully_parallel')
    elif partly:
        report.update(points_estimated=7, verdict='parked_partly_or_not_parallel')
    return report
