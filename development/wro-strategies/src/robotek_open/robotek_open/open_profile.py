"""Load Open v5 profiles and validate supported parameter names."""

from pathlib import Path

import yaml

from .v5.settings import validate_parameters


def load_parameters(profile, overrides):
    """Load a saved ROS profile, then apply explicit experiment overrides."""
    params = {}
    if profile:
        params.update(yaml.safe_load(Path(profile).read_text())[
            'open_strategy']['ros__parameters'])
    for item in overrides:
        key, value = item.split('=', 1)
        params[key] = yaml.safe_load(value)
    validate_parameters(params)
    return params
