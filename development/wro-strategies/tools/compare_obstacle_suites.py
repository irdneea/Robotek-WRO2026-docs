#!/usr/bin/env python3
"""Compare the Obstacle standard-set runs of several tags, per layout seed and direction.

    python3 tools/compare_obstacle_suites.py obs-base-a obs-base-b vs v2-a

Tags before `vs` form the reference group, tags after it the candidate group. Every field is a
`reg<seed>-<direction>` pair. For each field it prints points, validity, minimum clearance and the
time from Start of every run, the reference time range (min..max) widened by `--slack` seconds, and
a verdict. A candidate is also flagged when it scores fewer points than the reference, loses
validity, or keeps less clearance than the reference minus `--margin-slack` metres.

Rows are read from each round's `round.json` (the runner keeps telemetry local). When a tag was run
more than once for a field, the newest directory wins; the older attempts stay in the ledger.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'docs' / 'obstacle-challenge-runs'


def load(tag):
    rows = {}
    for directory in sorted(RUNS.glob(f'*-{tag}-reg*-*')):
        match = re.search(rf'-{re.escape(tag)}-(reg\d+-(?:ccw|cw))$', directory.name)
        round_file = directory / 'round.json'
        if not match or not round_file.exists():
            continue
        data = json.loads(round_file.read_text())
        judge = data.get('rule_judge') or {}
        validation = data.get('validation') or {}
        rows[match.group(1)] = dict(
            points=data.get('points_estimated'),
            time=judge.get('time_from_start_sim_seconds'),
            valid=validation.get('passed'),
            margin=validation.get('min_clearance_m'),
            margin_class=validation.get('margin_class'),
            failed=validation.get('failed') or [],
            name=directory.name,
        )
    return rows


def seed_key(field):
    seed, direction = field.split('-')
    return (int(seed[3:]), direction)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tags', nargs='+')
    parser.add_argument('--slack', type=float, default=5.0,
                        help='seconds added at each side of the reference time range (default 5.0)')
    parser.add_argument('--margin-slack', type=float, default=0.01,
                        help='metres of clearance a candidate may lose against the reference (default 0.01)')
    args = parser.parse_args()
    if 'vs' not in args.tags:
        parser.error('separate the reference tags from the candidate tags with the word vs')
    cut = args.tags.index('vs')
    reference, candidate = args.tags[:cut], args.tags[cut + 1:]
    ref = {tag: load(tag) for tag in reference}
    cand = {tag: load(tag) for tag in candidate}
    fields = sorted({name for runs in list(ref.values()) + list(cand.values()) for name in runs},
                    key=seed_key)

    bad = 0
    deltas = []
    print(f'{"field":10} {"ref pts/t":24} {"cand pts/t":24} {"ref m":7} {"cand m":7} verdict')
    for name in fields:
        ref_runs = [runs[name] for runs in ref.values() if name in runs]
        cand_runs = [runs[name] for runs in cand.values() if name in runs]
        ref_t = [r['time'] for r in ref_runs if r['time']]
        cand_t = [r['time'] for r in cand_runs if r['time']]
        ref_points = [r['points'] for r in ref_runs if r['points'] is not None]
        ref_valid = sum(1 for r in ref_runs if r['valid'])
        cand_valid = sum(1 for r in cand_runs if r['valid'])
        ref_margins = [r['margin'] for r in ref_runs if r['margin'] is not None]
        cand_margins = [r['margin'] for r in cand_runs if r['margin'] is not None]

        flags = []
        if ref_points and any((p or 0) < max(ref_points) for p in (r['points'] for r in cand_runs)):
            flags.append('points below reference')
        if cand_runs and len(cand_runs) != len(ref_runs):
            flags.append(f'{len(cand_runs)}/{len(ref_runs)} runs')
        outside = []
        lo, hi = (min(ref_t) - args.slack, max(ref_t) + args.slack) if ref_t else (0.0, 0.0)
        if ref_t and cand_t:
            deltas.extend(t - sum(ref_t) / len(ref_t) for t in cand_t)
            outside = [t for t in cand_t if not lo <= t <= hi]
            if outside:
                flags.append('time outside %.1f..%.1f' % (lo, hi))
        if ref_margins and cand_margins and min(cand_margins) < min(ref_margins) - args.margin_slack:
            flags.append('less clearance')
        if cand_runs and not all(r['valid'] for r in cand_runs):
            flags.append('invalid: ' + ','.join(sorted({f for r in cand_runs for f in r['failed']})))

        ref_text = ' '.join(f'{r["points"]}/{r["time"]:.1f}' if r['time'] else f'{r["points"]}/-'
                            for r in ref_runs)
        cand_text = ' '.join(f'{r["points"]}/{r["time"]:.1f}' if r['time'] else f'{r["points"]}/-'
                             for r in cand_runs)
        ref_m = f'{min(ref_margins)*100:.1f}' if ref_margins else '-'
        cand_m = f'{min(cand_margins)*100:.1f}' if cand_margins else '-'
        verdict = 'ok' if not flags else 'CHECK ' + '; '.join(flags)
        bad += verdict != 'ok'
        print(f'{name:10} {ref_text:24} {cand_text:24} {ref_m:7} {cand_m:7} {verdict}')

    print(f'\n{len(fields) - bad}/{len(fields)} fields consistent with the reference')
    print(f'valid rounds: reference {sum(sum(1 for r in runs.values() if r["valid"]) for runs in ref.values())}'
          f'/{sum(len(runs) for runs in ref.values())},'
          f' candidate {sum(sum(1 for r in runs.values() if r["valid"]) for runs in cand.values())}'
          f'/{sum(len(runs) for runs in cand.values())}')
    if deltas:
        print(f'mean difference candidate - reference: {sum(deltas) / len(deltas):+.2f} s '
              f'(largest {max(deltas, key=abs):+.2f} s) over {len(deltas)} runs')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
