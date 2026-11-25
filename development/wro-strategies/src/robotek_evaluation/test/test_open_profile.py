"""Check that the runner only takes Open v5 parameters: retired profiles and sources are rejected."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPEN_CONFIG = ROOT.parent / 'robotek_open' / 'config'
spec = importlib.util.spec_from_file_location('open_run_profile', ROOT / 'tools/run_gui_experiment.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_the_v5_profile_loads():
    assert runner.load_parameters(OPEN_CONFIG / 'open_v5.yaml', [])


def test_a_retired_v4_profile_is_rejected():
    # open_fastservo_v4 as recorded with its rounds (Open v4 was removed on 26 oct 2026).
    with pytest.raises(ValueError, match='Unsupported Open v5 parameters'):
        runner.load_parameters(ROOT.parents[1] / 'docs/open-challenge-runs/20261006T193850Z-std12-honest-fsv4-r1-square100-ccw/source/profile.yaml', [])


@pytest.mark.parametrize('override', ['distance_source=gt', 'yaw_source=orientation',
                                     'turn_front_heading_axis=false'])
def test_removed_sources_and_v4_switches_are_rejected(override):
    with pytest.raises(ValueError, match='Unsupported Open v5 parameters'):
        runner.load_parameters(OPEN_CONFIG / 'open_v5.yaml', [override])
