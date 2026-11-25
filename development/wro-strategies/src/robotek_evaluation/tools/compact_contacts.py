#!/usr/bin/env python3
"""Rewrite old contacts.jsonl logs (one line per physics-step message) as episodes.

Same grouping as the recorder (robotek_evaluation/contact_log.py). The judge and the
reports read both formats; this only shrinks the files (238 MB -> ~150 KB for a car
pressed against a wall). Logs that already hold episodes are left untouched.

    cd src/robotek_evaluation/tools && PYTHONPATH=.. python3 compact_contacts.py [contacts.jsonl ...]

Without arguments: every contacts.jsonl under docs/open-challenge-runs and
docs/obstacle-challenge-runs.
"""
import json
from pathlib import Path
import sys

from robotek_evaluation.contact_log import compact

ROOT = Path(__file__).resolve().parents[3]


def compact_file(path):
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    if not records or any('episode' in r for r in records):
        return None
    before = path.stat().st_size
    tmp = path.with_suffix('.jsonl.tmp')
    tmp.write_text(''.join(json.dumps(e)+'\n' for e in compact(records)))
    tmp.replace(path)
    return before, path.stat().st_size, len(records)


def main():
    paths = [Path(a) for a in sys.argv[1:]] or sorted(
        p for runs in ('open-challenge-runs', 'obstacle-challenge-runs')
        for p in (ROOT/'docs'/runs).glob('*/contacts.jsonl'))
    total_before = total_after = 0
    for path in paths:
        result = compact_file(path)
        if result is None:
            continue
        before, after, messages = result
        total_before += before
        total_after += after
        if before > 1e6:
            print(f'{path.parent.name[:70]:70s} {before/1e6:8.1f} MB -> {after/1e3:7.1f} KB ({messages} messages)')
    print(f'total {total_before/1e6:.1f} MB -> {total_after/1e6:.2f} MB')


if __name__ == '__main__':
    main()
