"""Check reproducible profile loading for the recorded GUI runner."""

import importlib.util
from pathlib import Path


def test_profile_preserves_auto_direction_and_explicit_overrides(tmp_path):
    path = Path(__file__).parents[1] / 'tools' / 'run_gui_experiment.py'
    spec = importlib.util.spec_from_file_location('gui_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profile = tmp_path / 'profile.yaml'
    profile.write_text('open_strategy:\n  ros__parameters:\n'
                       '    direction: auto\n    cruise_speed: 1.0\n'
                       '    done_hold: 35.0\n')
    params = module.load_parameters(profile, ['cruise_speed=0.9', 'auto_start=false'])
    assert params['direction'] == 'auto'
    assert params['cruise_speed'] == 0.9
    assert params['done_hold'] == 35.0
    assert params['auto_start'] is False
