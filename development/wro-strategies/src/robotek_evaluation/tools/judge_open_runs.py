#!/usr/bin/env python3
"""Re-judge saved Open Challenge rounds with the rule judge and the standard validation.

Writes <run>/rule_judge.json, adds ``rule_judge`` and ``validation`` to round.json
(``points_estimated`` becomes the rule-judge points; the previous winding-based
estimate is kept as ``points_estimated_legacy``) and refreshes rounds.jsonl in place.

    cd src/robotek_evaluation/tools && PYTHONPATH=.. python3 judge_open_runs.py [run-dir ...]
"""
import json
from pathlib import Path
import sys

from robotek_evaluation.open_round_report import add_rule_judge

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT/'docs/open-challenge-runs'


def judge_directory(directory):
    needed = [directory/n for n in ('manifest.json', 'telemetry.csv', 'events.jsonl', 'round.json')]
    if not all(p.exists() for p in needed):
        return None
    summary = json.loads((directory/'summary.json').read_text()) if (directory/'summary.json').exists() else {}
    report = add_rule_judge(directory, json.loads((directory/'round.json').read_text()), summary)
    (directory/'round.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    targets = [Path(a) for a in sys.argv[1:]] or sorted(p for p in RUNS.iterdir() if p.is_dir())
    updated = {}
    for directory in targets:
        report = judge_directory(directory)
        if report:
            updated[report['run']] = report
            v = report['validation']
            print('%-58s pts=%2s %-28s valid=%-5s %s' % (
                report['run'][:58], report['points_estimated'], report['rule_judge']['round_end']['reason']
                if report['rule_judge']['round_end'] else '-', v['passed'], ','.join(v['failed'])))
    path = RUNS/'rounds.jsonl'
    if path.exists() and updated:
        lines = []
        for line in path.read_text().splitlines():
            record = json.loads(line)
            lines.append(json.dumps(updated.get(record.get('run'), record)))
        path.write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    main()
