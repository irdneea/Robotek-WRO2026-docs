"""Persist round scores and Start-based timing separately from lap diagnostics."""

import csv
import json
import math

from .rule_judge import judge_open, load_contacts, standard_validation


def make_round_report(directory, summary):
    """Estimate fixed-field points; never present a simulator proxy as judge scoring."""
    telemetry = directory / 'telemetry.csv'
    rows = []
    if telemetry.exists():
        with telemetry.open() as stream:
            rows = list(csv.DictReader(stream))
    events_path = directory / 'events.jsonl'
    events = []
    if events_path.exists():
        events = [json.loads(line) for line in events_path.read_text().splitlines() if line]
    start = next((e for e in events if e['event'] == 'start'), None)
    done = next((e for e in events if e['event'] == 'done'), None)
    # Old runs have no Start event: do not substitute the first motion sample.
    end = done or (rows[-1] if rows else None)
    report = {
        'run': directory.name,
        'status': ('completed' if summary.get('completed') else
                   'incomplete' if start or summary.get('wall_time_seconds') is not None
                   else 'not_started_or_missing_start'),
        'start_source': start['source'] if start else 'not_recorded',
        'end_source': 'done_event' if done else 'last_sample' if end else 'no_data',
        'time_from_start_wall_seconds': None,
        'time_from_start_sim_seconds': None,
        'motion_wall_seconds': summary.get('wall_time_seconds'),
        'motion_sim_seconds': summary.get('sim_time_seconds'),
        'lap_splits': summary.get('lap_markers', []),
        'points_estimated': None,
        'points_official': None,
        'score_status': 'unverified_simulation_estimate',
        'points_breakdown': None,
        'limitations': [
            'Sections and laps estimated from ground-truth winding, not judged section exits.',
            'Contacts, wall movement, start legality and human repairs are not adjudicated.',
            'Finish bonus is provisional; DONE does not prove 30 seconds stationary.',
        ],
    }
    if start and end:
        for clock in ('wall', 'sim'):
            elapsed = float(end[clock + '_time']) - float(start[clock + '_time'])
            report['time_from_start_' + clock + '_seconds'] = max(0.0, elapsed)
    else:
        report['limitations'].append('Exact Start-to-end time unavailable.')
    winding = summary.get('gt_winding_laps')
    if winding is not None and math.isfinite(winding):
        # A completed, geometrically checked mission closes the final section;
        # partial runs retain the conservative angular-progress proxy.
        complete = bool(summary.get('validated_completed') and winding >= 2.85
                        and summary.get('turns', 0) >= 12)
        sections = 24 if complete else min(24, max(0, int(winding * 8)))
        laps = 3 if complete else min(3, max(0, int(winding)))
        finish = 3 if complete else 0
        if summary.get('direction_matches_test_orientation') is False:
            report['limitations'].append('Wrong selected direction: score cannot be inferred.')
        else:
            report['points_breakdown'] = {
                'sections_estimated': sections, 'laps_estimated': laps,
                'finish_provisional': finish,
            }
            report['points_estimated'] = sections + laps + finish
    elif rows and start and not any(float(r['v_cmd']) != 0 for r in rows):
        report['points_estimated'] = 0
        report['points_breakdown'] = {
            'sections_estimated': 0, 'laps_estimated': 0, 'finish_provisional': 0,
        }
    return report


def scoring_pose_rows(directory, telemetry, events):
    """Prefer independent audit poses to avoid missing short section crossings.

    This stream belongs to evaluation only. Strategy state comes from telemetry
    or the explicit DONE event; no audit pose is sent back to the controller.
    Older runs without a complete audit stream retain their telemetry fallback.
    """
    audit = directory / 'audit_pose.csv'
    if not audit.exists():
        return telemetry, 'telemetry.csv'
    with audit.open() as stream:
        poses = list(csv.DictReader(stream))
    required = ('sim_time', 'wall_time', 'x_gt', 'y_gt', 'yaw_gt',
                'steer_actual', 'steer_right_actual')
    poses = [p for p in poses if all(p.get(k) not in (None, '', 'nan')
             and math.isfinite(float(p[k])) for k in required)]
    poses.sort(key=lambda p: float(p['sim_time']))
    if not poses:
        return telemetry, 'telemetry.csv'
    if telemetry and (float(poses[0]['sim_time']) > float(telemetry[0]['sim_time']) + .2
                      or float(poses[-1]['sim_time']) < float(telemetry[-1]['sim_time']) - .2):
        return telemetry, 'telemetry.csv'
    done = next((float(e['sim_time']) for e in events if e['event'] == 'done'), math.inf)
    index = 0
    for pose in poses:
        t = float(pose['sim_time'])
        while index + 1 < len(telemetry) and float(telemetry[index + 1]['sim_time']) <= t:
            index += 1
        state = (telemetry[index].get('state', '') if telemetry
                 and float(telemetry[index]['sim_time']) <= t else '')
        pose['state'] = 'DONE' if t >= done else state
    return poses, 'audit_pose.csv'


def add_rule_judge(directory, report, summary):
    """Attach the rule judge and the standard validation; keep the old estimate."""
    manifest_path = directory / 'manifest.json'
    if not (manifest_path.exists() and (directory / 'telemetry.csv').exists()
            and (directory / 'events.jsonl').exists()):
        return report
    manifest = json.loads(manifest_path.read_text())
    with (directory / 'telemetry.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    events = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines() if line]
    scoring_rows, pose_source = scoring_pose_rows(directory, rows, events)
    judge = judge_open(directory, manifest, scoring_rows, events)
    judge.update(pose_source=pose_source, pose_sample_count=len(scoring_rows))
    contacts = load_contacts(directory)
    end = (judge.get('round_end') or {}).get('sim_time', float('inf'))
    touching = None if contacts is None else [c for c in contacts if c['sim_time'] <= end]
    validation = standard_validation(
        judge,
        dict(outer_wall=summary.get('min_outer_body_clearance_m'),
             inner_wall=summary.get('min_inner_body_clearance_m')),
        contacts is not None, touching, judge.get('stop_hold_sim_seconds'),
        summary.get('max_actual_steer_deg'))
    (directory / 'rule_judge.json').write_text(
        json.dumps(dict(rule_judge=judge, validation=validation), indent=2) + '\n')
    if 'points_estimated_legacy' not in report:
        report['points_estimated_legacy'] = report.get('points_estimated')
        report['points_breakdown_legacy'] = report.get('points_breakdown')
    report.update(points_estimated=judge['points'] if judge['round_end'] else None,
                  points_breakdown=judge['breakdown'] if judge['round_end'] else None,
                  score_status='simulation_rule_judge_v%d' % judge['version'],
                  rule_judge=judge, validation=validation)
    return report


def save_round_report(directory, summary):
    """Save one report and upsert the shared ledger, including failed attempts."""
    report = add_rule_judge(directory, make_round_report(directory, summary), summary)
    (directory / 'round.json').write_text(json.dumps(report, indent=2) + '\n')
    ledger = directory.parent / 'rounds.jsonl'
    records = {}
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            if line:
                record = json.loads(line)
                records[record['run']] = record
    records[report['run']] = report
    temporary = ledger.with_suffix('.jsonl.tmp')
    temporary.write_text(''.join(
        json.dumps(records[key]) + '\n' for key in sorted(records)
    ))
    temporary.replace(ledger)
    return report
