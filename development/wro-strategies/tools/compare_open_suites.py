#!/usr/bin/env python3
"""Compare the Open standard-set runs of several tags, per field and direction.

    python3 tools/compare_open_suites.py refbase-a refbase-b vs refac-a refac-b

Tags before `vs` form the reference group, tags after it the candidate group. For every
field/direction it prints points, validity, margin class and the time from Start of each run,
the reference range (min..max) and whether the candidate times fall inside it widened by
`--slack` seconds (default 1.0: two identical runs of the 12-round set differed by up to 1.0 s on a field). Rounds are noisy (sensor noise differs between runs), so a candidate
is judged against the spread of the reference runs, not against one number.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'docs' / 'open-challenge-runs'


def load(tag):
    rows = {}
    for directory in sorted(RUNS.glob(f'*-std12-{tag}-*')):
        match = re.search(rf'std12-{re.escape(tag)}-(.+)$', directory.name)
        round_file = directory / 'round.json'
        if not match or not round_file.exists():
            continue
        data = json.loads(round_file.read_text())
        judge = data.get('rule_judge') or {}
        validation = data.get('validation') or {}
        rows[match.group(1)] = dict(points=data.get('points_estimated'),
                                    time=judge.get('time_from_start_sim_seconds'),
                                    valid=validation.get('passed'),
                                    margin=validation.get('margin_class'))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tags', nargs='+')
    parser.add_argument('--slack', type=float, default=1.0)
    args = parser.parse_args()
    if 'vs' not in args.tags:
        parser.error('separate the reference tags from the candidate tags with the word vs')
    cut = args.tags.index('vs')
    reference, candidate = args.tags[:cut], args.tags[cut + 1:]
    ref = {t: load(t) for t in reference}
    cand = {t: load(t) for t in candidate}
    fields = sorted({name for runs in list(ref.values()) + list(cand.values()) for name in runs})
    bad = 0
    deltas = []
    print(f'{"field-direction":22} {"reference times":22} {"candidate times":22} verdict')
    for name in fields:
        rt = [r[name]['time'] for r in ref.values() if name in r and r[name]['time']]
        ct = [r[name]['time'] for r in cand.values() if name in r and r[name]['time']]
        flags = []
        for group in list(ref.values()) + list(cand.values()):
            if name in group:
                run = group[name]
                if run['points'] != 30 or not run['valid']:
                    flags.append(f'points={run["points"]} valid={run["valid"]}')
        lo, hi = (min(rt) - args.slack, max(rt) + args.slack) if rt else (0, 0)
        if rt and ct:
            deltas.append(sum(ct) / len(ct) - sum(rt) / len(rt))
        outside = [t for t in ct if not lo <= t <= hi]
        verdict = 'ok' if not flags and not outside else 'CHECK ' + '; '.join(
            flags + [f'{t:.2f} outside {lo:.2f}..{hi:.2f}' for t in outside])
        bad += verdict != 'ok'
        print(f'{name:22} {" ".join(f"{t:6.2f}" for t in rt):22} {" ".join(f"{t:6.2f}" for t in ct):22} {verdict}')
    print(f'\n{len(fields) - bad}/{len(fields)} field-directions consistent with the reference spread')
    if deltas:
        print(f'mean difference candidate - reference: {sum(deltas) / len(deltas):+.3f} s '
              f'(largest {max(deltas, key=abs):+.2f} s) over {len(deltas)} field-directions')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
