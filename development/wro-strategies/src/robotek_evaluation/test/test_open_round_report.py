"""Check round timing, incomplete attempts and durable score records."""

import csv
import json

from robotek_evaluation.open_round_report import make_round_report, save_round_report


def write_run(tmp_path, events, rows):
    directory = tmp_path / 'trial'
    directory.mkdir()
    (directory / 'events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
    if rows:
        with (directory / 'telemetry.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return directory


def test_start_timing_includes_calibration_and_excludes_done_hold(tmp_path):
    directory = write_run(tmp_path, [
        {'event': 'start', 'source': 'start_topic', 'wall_time': 10, 'sim_time': 5},
        {'event': 'done', 'source': 'state_machine', 'wall_time': 90, 'sim_time': 75},
    ], [{'wall_time': 120, 'sim_time': 105, 'v_cmd': 0}])
    report = make_round_report(directory, {
        'completed': True, 'validated_completed': True, 'gt_winding_laps': 2.98,
        'wall_time_seconds': 77, 'turns': 12,
    })
    assert report['time_from_start_wall_seconds'] == 80
    assert report['time_from_start_sim_seconds'] == 70
    assert report['points_estimated'] == 30
    assert report['points_official'] is None
    assert report['points_breakdown']['finish_provisional'] == 3


def test_failed_round_records_elapsed_and_partial_points(tmp_path):
    directory = write_run(tmp_path, [
        {'event': 'start', 'source': 'auto_first_scan', 'wall_time': 10, 'sim_time': 5},
    ], [{'wall_time': 50, 'sim_time': 40, 'v_cmd': 0.2}])
    report = make_round_report(directory, {'gt_winding_laps': 1.25})
    assert report['status'] == 'incomplete'
    assert report['end_source'] == 'last_sample'
    assert report['time_from_start_wall_seconds'] == 40
    assert report['points_estimated'] == 11


def test_legacy_no_start_does_not_invent_regulation_time(tmp_path):
    directory = write_run(tmp_path, [], [])
    report = make_round_report(directory, {'completed': True, 'wall_time_seconds': 68.5})
    assert report['time_from_start_wall_seconds'] is None
    assert report['motion_wall_seconds'] == 68.5
    assert report['points_estimated'] is None


def test_ledger_updates_without_duplicates_and_keeps_failed_attempt(tmp_path):
    directory = write_run(tmp_path, [], [])
    save_round_report(directory, {'completed': False})
    save_round_report(directory, {'completed': True})
    records = (tmp_path / 'rounds.jsonl').read_text().splitlines()
    assert len(records) == 1
    assert json.loads(records[0])['status'] == 'completed'


def test_wrong_direction_does_not_claim_points(tmp_path):
    directory = write_run(tmp_path, [], [])
    report = make_round_report(directory, {
        'gt_winding_laps': 2.98, 'direction_matches_test_orientation': False,
    })
    assert report['points_estimated'] is None


def test_duplicate_start_does_not_reset_round_timer():
    from types import SimpleNamespace

    from robotek_open.v5.node import OpenV5Node

    events = []
    mission = SimpleNamespace(started=False)

    def start():
        mission.started = True

    mission.request_start = start
    recording = SimpleNamespace(record_event=lambda *args: events.append(args[:2]))
    node = SimpleNamespace(mission=mission, recording=recording, sim_seconds=0.0)
    OpenV5Node.request_start(node, 'start_topic')
    OpenV5Node.request_start(node, 'start_topic')
    assert events == [('start', 'start_topic')]
