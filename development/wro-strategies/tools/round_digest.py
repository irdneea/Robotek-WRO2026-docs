#!/usr/bin/env python3
"""Short digest of Open and Obstacle rounds: read this instead of round.json (3-13 KB) or the
telemetry and planner files (~100k tokens each).

    python3 tools/round_digest.py <round> [<round> ...]       # 4-5 lines per round
    python3 tools/round_digest.py <round> --at fault           # plus a table around the first fault
    python3 tools/round_digest.py <round> --at 7.3 --span 1.5 --every 0.25

<round> is a round directory, or the end of its name (``cap-ref-reg0-ccw``: the newest match in
docs/obstacle-challenge-runs or docs/open-challenge-runs). A lab round directory (telemetry.csv
without round.json) works too. Obstacle: the table compares the strategy's pose with the recorded
ground truth (CW rounds run in a mirrored track frame: x and the heading are mirrored back). Open:
the v5 keeps no pose, so the table shows the ground truth, the wall distances and the turn reason.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/robotek_common'))
from robotek_common.vehicle import WHEELBASE  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / 'docs'
RUNS = (DOCS / 'obstacle-challenge-runs', DOCS / 'open-challenge-runs')


def find(name):
    path = Path(name)
    if path.is_dir():
        return path
    matches = sorted((p for runs in RUNS for p in runs.glob(f'*{name}')), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise SystemExit(f'no round matches {name}')
    return matches[-1]


def _float(row, key):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return math.nan


def pose_errors(row):
    """(position error m, heading error rad) of the strategy's pose against the ground truth."""
    x, y, th = _float(row, 'x_track'), _float(row, 'y_track'), _float(row, 'th_track')
    if row.get('selected_direction') == 'cw':
        x, th = -x, math.pi - th
    gx, gy, gyaw = _float(row, 'x_gt'), _float(row, 'y_gt'), _float(row, 'yaw_gt')
    yaw = math.atan2(math.sin(th - gyaw), math.cos(th - gyaw))
    return math.hypot(x - gx, y - gy), yaw


def _cm(value):
    return '-' if value is None or not math.isfinite(value) else f'{100 * value:.1f}'


def summary(directory, rows):
    lines = []
    try:
        r = json.load(open(directory / 'round.json'))
    except OSError:
        r = {}
    judge, valid = r.get('rule_judge') or {}, r.get('validation') or {}
    parts = (r.get('points_breakdown_estimated') or judge.get('breakdown') or {}).values()
    breakdown = '+'.join('-' if p is None else str(p) for p in parts)
    t = judge.get('time_from_start_sim_seconds')
    lines.append(f"{directory.name} | {judge.get('challenge', '?')} {r.get('direction', '')} | pts {r.get('points_estimated', '?')} ({breakdown}) "
                 f"| valid {valid.get('passed', '?')} {valid.get('margin_class', '')} "
                 f"| t {t:.1f} s sim" if t else f"{directory.name} | pts {r.get('points_estimated', '?')} | no time")
    laps = ' '.join(f"{lap['sim_seconds']:.1f}" if 'sim_seconds' in lap else f"{lap.get('wall_seconds', 0):.1f}w"
                    for lap in r.get('lap_splits') or [])   # w: wall seconds (the Open records only those)
    checks = valid.get('checks') or {}
    clear = [f"{k.replace('min_', '').replace('_clearance_m', '')} {_cm(c.get('value'))}"
             for k, c in checks.items() if k.endswith('clearance_m')]
    if r.get('min_sampled_pillar_clearance_m') is not None:
        clear.insert(0, f"sign {_cm(r['min_sampled_pillar_clearance_m'])}")
    steer = (checks.get('steering_limit') or {}).get('value') or r.get('max_steer_degrees') or 0
    lines.append(f"laps {laps or '-'} | clearance cm: {', '.join(clear) or '-'} | steer max {steer:.1f} deg "
                 f"| end {(judge.get('round_end') or {}).get('reason', '-')}")
    problems = list(valid.get('failed') or [])
    problems += [f"{f.get('fault') or f.get('type')}:{f.get('pillar') or ''}@{f.get('sim_time', '?')}"
                 for f in judge.get('faults') or []]
    contact = first_contact(directory)
    if contact:
        problems.append(f"contact {contact[1]}@{contact[0]:.2f}")
    if r.get('stopped_on_pillar_fault'):
        problems.append(f"stopped: {r['stopped_on_pillar_fault'].get('pillar')} left its circle")
    if problems:
        lines.append('problems: ' + ', '.join(problems))
    states = [row.get('state', '') for row in rows]
    states = [s for i, s in enumerate(states) if s and (i == 0 or s != states[i - 1])]
    lines.append(f"telemetry {len(rows)} rows, states {'>'.join(states[:12]) or '-'}"
                 + ('' if rows else f" | launch.log: {last_error(directory)}"))
    if rows and 'turns' in rows[0]:
        lines.append(f"turns {rows[-1].get('turns', '?')}, direction {rows[-1].get('selected_direction', '?')}")
    if not rows or 'x_track' not in rows[0]:
        return lines
    errors = [pose_errors(row) for row in rows if row.get('state') not in ('', 'SETUP', 'WAIT')]
    errors = [e for e in errors if math.isfinite(e[0])]
    if errors:
        worst = max(range(len(errors)), key=lambda i: errors[i][0])
        lines.append(f"pose error median {100 * statistics.median(e[0] for e in errors):.1f} cm, max "
                     f"{100 * errors[worst][0]:.1f} cm; heading max {math.degrees(max(abs(e[1]) for e in errors)):.1f} deg")
    return lines


def last_error(directory):
    """Last line of launch.log that looks like an error (why a round left no telemetry)."""
    try:
        lines = (directory / 'launch.log').read_text(errors='replace').splitlines()
    except OSError:
        return 'no launch.log'
    hits = [l for l in lines if any(w in l for w in ('ERROR', 'Error', 'error:', 'Traceback', 'died', 'exception'))]
    return (hits[-1] if hits else lines[-1] if lines else 'empty')[:160]


def first_contact(directory):
    """(sim time, what) of the first contact recorded in contacts.jsonl, if any."""
    try:
        with open(directory / 'contacts.jsonl') as f:
            for line in f:
                c = json.loads(line)
                what = c.get('pillar') or (c.get('other') or '').split('::')[-1] or c.get('kind')
                return float(c.get('sim_time', math.nan)), what
    except (OSError, ValueError):
        pass
    return None


def fault_time(directory):
    try:
        r = json.load(open(directory / 'round.json'))
        faults = (r.get('rule_judge') or {}).get('faults') or []
        if faults and faults[0].get('sim_time') is not None:
            return float(faults[0]['sim_time'])
    except (OSError, ValueError):
        pass
    contact = first_contact(directory)
    return contact[0] if contact else None


def open_table(rows, at, span, every):
    """Open v5 (no pose estimate): ground truth, wall distances, command and turn reason."""
    out = ['    t state   turn  x_gt   y_gt  yaw | front  left right |    v  steer reason']
    last = -math.inf
    for row in rows:
        t = _float(row, 'sim_time')
        if not at - span <= t <= at + span or t - last < every - 1e-9:
            continue
        last = t
        v, w = _float(row, 'v_cmd'), _float(row, 'w_cmd')
        steer = math.degrees(math.atan(w * WHEELBASE / v)) if abs(v) > 1e-3 else 0.0
        out.append(f"{t:5.1f} {row.get('state', '')[:7]:<7} {row.get('turns', ''):>2} "
                   f"{_float(row, 'x_gt'):6.3f} {_float(row, 'y_gt'):6.3f} {math.degrees(_float(row, 'yaw_gt')):5.0f} "
                   f"| {_float(row, 'front'):5.2f} {_float(row, 'left'):5.2f} {_float(row, 'right'):5.2f} "
                   f"| {v:+.2f} {steer:+5.1f} {row.get('turn_reason', '')[:20]}")
    return out


def table(rows, at, span, every):
    if rows and 'x_track' not in rows[0]:
        return open_table(rows, at, span, every)
    out = ['    t state  phi     x      y    yaw | err cm  deg |    v  steer']
    last = -math.inf
    for row in rows:
        t = _float(row, 'sim_time')
        if not at - span <= t <= at + span or t - last < every - 1e-9:
            continue
        last = t
        e, de = pose_errors(row)
        v, w = _float(row, 'v_cmd'), _float(row, 'w_cmd')
        steer = math.degrees(math.atan(w * WHEELBASE / v)) if abs(v) > 1e-3 else 0.0
        out.append(f"{t:5.1f} {row.get('state', '')[:5]:<5} {_float(row, 'progress'):5.2f} "
                   f"{_float(row, 'x_track'):6.3f} {_float(row, 'y_track'):6.3f} {math.degrees(_float(row, 'th_track')):5.0f} "
                   f"| {100 * e:5.1f} {math.degrees(de):4.1f} | {v:+.2f} {steer:+5.1f}")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('rounds', nargs='+')
    parser.add_argument('--at', help="sim time of the table, or 'fault' (first fault or contact)")
    parser.add_argument('--span', type=float, default=1.0, help='s before and after --at')
    parser.add_argument('--every', type=float, default=0.2, help='s between table rows')
    args = parser.parse_args()
    for name in args.rounds:
        directory = find(name)
        try:
            rows = list(csv.DictReader(open(directory / 'telemetry.csv')))
        except OSError:
            rows = []
        print('\n'.join(summary(directory, rows)))
        if args.at:
            at = fault_time(directory) if args.at == 'fault' else float(args.at)
            if at is None:
                print('no fault or contact')
            else:
                print('\n'.join(table(rows, at, args.span, args.every)))


if __name__ == '__main__':
    main()
