#!/usr/bin/env python3
"""Recompute round reports from raw records, without launching a simulation.

Only full rounds are recomputed; old straight-section component tests keep their saved report.

    audit_obstacle_runs.py                 # all rounds
    audit_obstacle_runs.py '*-obs-base-*'  # only directories matching the glob (ledger kept for the rest)
"""
import fnmatch
import json
import sys
from run_obstacle_gui_experiment import RUNS, summarize, write_json  # noqa: E402
pattern=sys.argv[1] if len(sys.argv)>1 else '*'
reports=[]
for directory in sorted(RUNS.iterdir()):
    if not (directory/'manifest.json').exists(): continue
    manifest=json.loads((directory/'manifest.json').read_text())
    prior=json.loads((directory/'round.json').read_text()) if (directory/'round.json').exists() else {}
    if not fnmatch.fnmatch(directory.name,pattern):
        if prior: reports.append(prior)
        continue
    if manifest.get('scope')!='round':
        if prior: reports.append(prior)
        continue
    report=summarize(directory,manifest)
    report.update(name=manifest['name'],directory=str(directory),direction=manifest['direction'],
                  color=manifest['pillar']['color'] if manifest.get('pillar') else manifest.get('layout'),launch_exit_code=prior.get('launch_exit_code'),
                  postprocessed_from_raw=True)
    # Keep what only the runner measured (launch wall time, live stop, timeout).
    for key in ('launch_wall_seconds','stopped_on_pillar_fault','wall_timeout_reached'):
        if key in prior: report[key]=prior[key]
    if prior.get('verdict',report.get('verdict'))!=report.get('verdict'):
        report['previous_verdict']=prior.get('verdict')
    if (directory/'INTERRUPTED.md').exists():
        # Stopped by hand before the round ended: keep the data, never score it.
        report.update(interrupted=True,points_estimated=None,full_round_validated=False,
                      runner_note=(directory/'INTERRUPTED.md').read_text().strip())
        if 'validation' in report:
            report['validation']['passed']=False
            report['validation']['failed']=['interrupted']
    if not prior:
        report['runner_note']='Recovered from raw logs; runner interrupted after node shutdown, launch exit code unknown.'
    write_json(directory/'round.json',report)
    reports.append(report)
(RUNS/'rounds.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in reports))
for r in reports:
    print(json.dumps({k:r.get(k) for k in ('name','component_pass','timings','points_estimated','min_sampled_pillar_clearance_m','min_sampled_wall_clearance_m','pillar_max_horizontal_motion_m')}))
