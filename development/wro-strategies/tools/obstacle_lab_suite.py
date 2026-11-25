#!/usr/bin/env python3
"""Obstacle lab over a set of fields and noise seeds, in parallel, from the source tree.

    python3 tools/obstacle_lab_suite.py                         # standard set: layouts 0-4 x ccw/cw, seed 0
    python3 tools/obstacle_lab_suite.py --seeds 0-4             # the 50 rounds of phase 4
    python3 tools/obstacle_lab_suite.py --layouts 5-24 --early  # held-out layouts, stop at the first fault
    python3 tools/obstacle_lab_suite.py --fields reg2-ccw,reg3-cw --param pillar_clearance=0.2

Fields are generated with the runner's own layout generator (``regulation_signs``), so layout N is
the field of the Gazebo rounds ``reg<N>-<direction>`` (spawn -0.25 m, as the standard set); the
layouts after 4 are a held-out set nobody tuned on. The strategy is imported from ``src`` (never the
installed copy, which may be stale). ``--early`` ends a round 1.5 s after a clear wrong-side pass;
the judge still scores it. ``--out`` keeps the JSON, ``--against`` prints the change per field;
``--brief`` prints only the changed rounds (or, without ``--against``, the invalid ones): use it by default.
While it runs, a progress line goes to stderr at most every 2 s (rounds done, %, valid, parked, time left); ``--quiet`` hides it.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [str(ROOT / 'src' / p) for p in ('robotek_obstacle', 'robotek_evaluation', 'robotek_common')]


def _use_sources():
    for path in reversed(SOURCES):
        if path not in sys.path:
            sys.path.insert(0, path)
    os.environ['PYTHONPATH'] = os.pathsep.join(SOURCES + [os.environ.get('PYTHONPATH', '')])


def _span(text):
    out = []
    for part in text.split(','):
        if part.startswith('-'):
            out.append(int(part))
            continue
        low, _, high = part.partition('-')
        out.extend(range(int(low), int(high or low) + 1))
    return out


def make_field(base, layout, direction, parking=False, shift=(0.0, 0.0)):
    """Round directory (world.sdf + manifest.json) of a regulation layout, with the lot if asked;
    layout -1 is the lot alone (no signs). ``shift`` (dx, dy) m moves the bottom outer wall by dy and the
    lot by (dx, dy) in the world frame (a field built off the rules: on the car, 8 nov 2026, the outer
    wall showed 2-7 cm out and a limit ~3 cm off)."""
    from robotek_evaluation.obstacle_experiment_setup import PARKING_LOT, build_parking_world, build_world
    tag = '' if not any(shift) else '-shift%+.3f%+.3f' % tuple(shift)
    # The lot is in the name: fields are cached, and a cached field of another lot (10 nov 2026: the lot went from
    # 0.3495 to 0.3675 m) would put the limits where the strategy does not expect them.
    park = '-park%.4f' % (PARKING_LOT['x1'] - PARKING_LOT['x0']) if parking else ''
    directory = Path(base) / (f'reg{layout}-{direction}' + park + tag)
    if not (directory / 'manifest.json').exists():
        directory.mkdir(parents=True, exist_ok=True)
        pillars = build_parking_world(directory, ROOT) if layout < 0 else build_world(directory, layout, ROOT, parking)
        lot = PARKING_LOT if parking else None
        if any(shift):
            lot = _shift_field(directory / 'world.sdf', lot, *shift)
        manifest = dict(direction=direction, seed=layout, pillars=pillars, spawn_progress=-0.25,
                        parking_lot=lot, field_shift=list(shift) if any(shift) else None)
        (directory / 'manifest.json').write_text(json.dumps(manifest))
    return directory


def _shift_field(world_sdf, lot, dx, dy):
    """Move the bottom outer wall by dy and the lot limits by (dx, dy) in a world.sdf; -> the moved lot."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(world_sdf)
    for node in tree.getroot().iter('collision'):
        if node.get('name', '').startswith('wall_ext_south'):
            pose = node.find('pose')
            v = [float(a) for a in pose.text.split()]
            v[1] += dy
            pose.text = ' '.join(str(a) for a in v)
    for link in tree.getroot().findall(".//model[@name='parking_lot']/link"):
        pose = link.find('pose')
        v = [float(a) for a in pose.text.split()]
        v[0] += dx
        v[1] += dy
        pose.text = ' '.join(str(a) for a in v)
    tree.write(world_sdf, encoding='unicode', xml_declaration=True)
    if lot is None:
        return None
    return dict(x0=lot['x0'] + dx, x1=lot['x1'] + dx, y0=lot['y0'] + dy, y1=lot['y1'] + dy)


def _job(args):
    _use_sources()
    from robotek_evaluation.obstacle_lab import run_round
    field, directory, seed, strategy, overrides, early, tmax, occlusion, car_name, car_overrides = args
    car = None
    if car_name:
        from robotek_evaluation.open_lab import car_profile
        car = car_profile(car_name, car_overrides)
    started = time.process_time()
    result = run_round(directory, seed=seed, overrides=overrides, strategy_name=strategy,
                       stop_on_fault=early, tmax=tmax, occlusion=occlusion, car=car)
    faults = result['faults']
    park = result.get('parking') or {}
    reason = faults[0]['fault'] + ':' + str(faults[0].get('pillar') or '') if faults else \
        ('contact:' + str((result['contact'] or {}).get('pillar') or (result['contact'] or {}).get('kind'))
         if result['contact'] else ','.join(result['failed']))
    return dict(field=field, seed=seed, points=result['points'], time=result['time'],
                valid=result['valid'], clearance=result['measured_clearance'],
                contact_time=result['contact_time'], reason=reason, park=park.get('verdict'),
                resets=result.get('board_resets', 0),
                cpu=round(time.process_time() - started, 1))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--layouts', default='0-4')
    parser.add_argument('--directions', default='ccw,cw')
    parser.add_argument('--fields', help='comma list like reg2-ccw,reg0-cw (overrides layouts)')
    parser.add_argument('--seeds', default='0')
    parser.add_argument('--strategy', default='v3', choices=['v3', 'v2', 'current'])
    parser.add_argument('--param', action='append', default=[], help='name=value override')
    parser.add_argument('--early', action='store_true', help='stop a round after a clear wrong-side pass')
    parser.add_argument('--parking', action='store_true', help='fields with the parking lot; the car parks')
    parser.add_argument('--tmax', type=float, default=180.0, help='simulated seconds (cut a round to a corner)')
    parser.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument('--out', type=Path)
    parser.add_argument('--field-shift', type=lambda t: tuple(float(v) for v in t.split(',')), default=(0.0, 0.0),
                        metavar='DX,DY', help='move the bottom outer wall by DY and the lot by (DX, DY) m, world frame')
    parser.add_argument('--no-occlusion', action='store_true',
                        help='camera sees through walls and signs (the lab before 26 oct 2026)')
    parser.add_argument('--car', choices=['real_v1', 'real_v2', 'real_v3', 'real_v4'],
                        help='car profile of open_lab (default: the Gazebo car, as before); real_v2 = the real car of 4 nov 2026, real_v3 = since 8 nov 2026, real_v4 = since 11 nov 2026')
    parser.add_argument('--car-param', action='append', default=[], help='name=value override of the car profile')
    parser.add_argument('--against', type=Path, help='previous --out JSON to compare with')
    parser.add_argument('--brief', action='store_true',
                        help='print only rounds whose points or validity changed (with --against), else only invalid ones')
    parser.add_argument('--quiet', action='store_true', help='no progress lines on stderr')
    args = parser.parse_args(argv)
    _use_sources()
    import yaml
    overrides = {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.param)}
    if args.parking and args.strategy in ('v2', 'v3'):
        overrides.setdefault('park', 1.0)
    if args.fields:
        fields = [(int(f.rsplit('-', 1)[0][3:]), f.rsplit('-', 1)[1]) for f in args.fields.split(',')]
    else:
        fields = [(n, d) for n in _span(args.layouts) for d in args.directions.split(',')]
    base = Path(tempfile.gettempdir()) / 'obstacle-lab-fields'
    jobs = []
    for layout, direction in fields:
        directory = make_field(base, layout, direction, args.parking, args.field_shift)
        for seed in _span(args.seeds):
            jobs.append((f'reg{layout}-{direction}', str(directory), seed, args.strategy, overrides, args.early, args.tmax,
                         not args.no_occlusion, args.car,
                         {k: yaml.safe_load(v) for k, v in (p.split('=', 1) for p in args.car_param)}))
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_job, job): i for i, job in enumerate(jobs)}
        results, shown = [None] * len(jobs), 0.0
        for done, future in enumerate(as_completed(futures), 1):
            results[futures[future]] = future.result()
            elapsed = time.time() - started
            if not args.quiet and (done == len(jobs) or elapsed - shown >= 2.0):
                shown = elapsed
                finished = [r for r in results if r is not None]
                parked = sum(1 for r in finished if r.get('park') == 'parked_fully_parallel')
                print('progress %d/%d (%.0f%%)  valid %d%s  %.0f s, ~%.0f s left' % (
                    done, len(jobs), 100.0 * done / len(jobs), sum(1 for r in finished if r['valid']),
                    '  fully parked %d' % parked if args.parking else '', elapsed,
                    elapsed / done * (len(jobs) - done)), file=sys.stderr, flush=True)
    wall = time.time() - started
    previous = {}
    if args.against and args.against.exists():
        previous = {(r['field'], r['seed']): r for r in json.loads(args.against.read_text())['results']}
    for r in results:
        old = previous.get((r['field'], r['seed']))
        same = old is not None and (old['points'], old['valid']) == (r['points'], r['valid'])
        if args.brief and (same if old is not None else r['valid']):
            continue
        change = '' if old is None else ('  was %s %s' % (old['points'], 'valid' if old['valid'] else 'invalid'))
        print('%-10s s%-2d pts=%-3s t=%-6s %-7s m=%-7s %-28s%s' % (
            r['field'], r['seed'], r['points'], '%.1f' % r['time'] if r['time'] else '-',
            'VALID' if r['valid'] else 'invalid',
            '%.1fcm' % (r['clearance'] * 100) if r['clearance'] is not None else '-',
            ('' if r['valid'] else r['reason']) + (' park=%s' % r['park'] if r.get('park') else '')
            + (' resets=%d' % r['resets'] if r.get('resets') else ''), change))
    valid = [r for r in results if r['valid']]
    times = [r['time'] for r in valid if r['time']]
    was = ''
    if previous:
        old_valid = sum(1 for r in results if previous.get((r['field'], r['seed']), {}).get('valid'))
        was = '  (was %d)' % old_valid
    print('valid %d/%d%s  mean time valid %.1f s  cpu %.0f s  wall %.0f s (%d workers)' % (
        len(valid), len(results), was, sum(times) / len(times) if times else 0.0,
        sum(r['cpu'] for r in results), wall, args.workers))
    if args.out:
        args.out.write_text(json.dumps(dict(args=vars(args) | {'out': str(args.out), 'against': str(args.against)},
                                            results=results), indent=1, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
