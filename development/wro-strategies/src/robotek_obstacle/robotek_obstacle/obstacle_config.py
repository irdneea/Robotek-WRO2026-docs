"""Parameters of the Obstacle strategy; defaults are the obstacle_planner_v8 values.

Only the tunable fields are ROS parameters; the fixed values were never changed in
any profile and are class constants (tests may override them per instance).

Units: metres, seconds, radians. +steer turns left (counter-clockwise).
"""
from dataclasses import dataclass, fields
from typing import ClassVar, get_origin
from pathlib import Path

import yaml

from robotek_common.vehicle import CAMERA_HFOV, CAMERA_PITCH


@dataclass
class ObstacleConfig:
    # ---- Tunable parameters (ROS parameters; a profile may set them) ----
    # Speed on the planned path
    plan_speed: float = 0.50  # m/s cap
    plan_lat_accel: float = 0.35  # m/s^2 in curves
    plan_brake: float = 0.6  # m/s^2 to the end of the path / the goal
    finish_speed: float = 0.18  # m/s for the last 0.3 track units
    # Clearance kept by the search
    plan_wall_margin: float = 0.03  # m hard clearance to walls
    plan_pillar_margin: float = 0.04  # m hard clearance to signs
    plan_soft: float = 0.05  # m of extra soft clearance
    plan_terminal_heading_cost: float = 3.0  # end-of-horizon misalignment with the lane
    # Parking (obstacle_parking.py)
    mode: str = 'laps'            # 'laps' (three laps, stop) or 'park' (parking only, test world)
    park_speed: float = 0.06      # m/s while manoeuvring in the lot
    park_margin: float = 0.015    # m kept from the limits and the wall by the parking search
    # Steering latency compensation
    plan_latency: float = 0.0  # s steering latency: feedforward of the planned steer ahead
    # Camera geometry for the sign bearings (defaults: the simulated camera, vehicle.py).
    # Real car: vehicle.py REAL_CAMERA_* (real_car:=true and robot.launch.py pass them).
    camera_hfov: float = CAMERA_HFOV
    camera_pitch: float = CAMERA_PITCH
    camera_yaw: float = 0.0  # rad, camera turned left (+) of the LiDAR's zero
    # Steering: rule limit 25 deg; the real car reaches ~17.6 deg (vehicle.REAL_STEER_LIMIT).
    steer_limit: float = 0.4363323129985824

    # ---- Fixed values (not parameters): never tuned in any profile; edit here ----
    # Mission
    laps: ClassVar[int] = 3
    calibrate_seconds: ClassVar[float] = 1.0  # still, to estimate the gyro bias
    direction_timeout: ClassVar[float] = 15.0  # s without a CW/CCW decision -> fault
    plan_direction_margin: ClassVar[float] = 0.10  # wall-fit inlier gap to trust the lidar direction
    # Camera fallback for the direction: creep straight while the lines are read.
    direction_probe_speed: ClassVar[float] = 0.10
    heading_kp: ClassVar[float] = 1.8
    heading_kd: ClassVar[float] = 0.2
    vision_min_length: ClassVar[float] = 40.0  # px of a coloured line
    vision_min_confidence: ClassVar[float] = 0.25
    vision_confirmations: ClassVar[int] = 5  # consecutive frames
    # Driving the planned path
    plan_lookahead: ClassVar[float] = 0.16  # m pure-pursuit lookahead at rest
    plan_feedback: ClassVar[float] = 0.6  # pure-pursuit correction gain when feedforward is on
    plan_stop_x: ClassVar[float] = 0.20  # m along the start straight to stop at
    plan_finish_zone: ClassVar[float] = 1.5  # track units before the stop labelled FINISH
    recover_speed: ClassVar[float] = 0.15  # m/s reversing when no path exists
    plan_recover_distance: ClassVar[float] = 0.25  # m reversed if no reverse arc helps
    # Localization
    plan_loc_gain: ClassVar[float] = 0.5  # wall-fit correction blended per scan
    # Search
    plan_period: ClassVar[float] = 0.10  # s of simulated time between replans (inside the control step)
    plan_ds: ClassVar[float] = 0.08  # m per search step
    plan_steps: ClassVar[int] = 22  # horizon in steps
    plan_beam: ClassVar[int] = 60
    plan_cell: ClassVar[float] = 0.05  # m; the beam keeps one node per cell
    plan_steer_step: ClassVar[float] = 0.20  # rad max steering change per step
    plan_wall_cost: ClassVar[float] = 400.0
    plan_pillar_cost: ClassVar[float] = 800.0
    plan_steer_cost: ClassVar[float] = 0.05
    plan_rate_cost: ClassVar[float] = 0.5
    plan_progress_gain: ClassVar[float] = 10.0
    plan_side_cost: ClassVar[float] = 300.0  # wrong side of a known sign while approaching
    plan_side_window: ClassVar[float] = 0.9  # m before the sign's radius line
    plan_view_gain: ClassVar[float] = 2.0  # reward per m with an unknown sign in view
    plan_unknown_cost: ClassVar[float] = 40.0  # approach an unknown-colour sign in line


def validate_parameters(params, allowed=()):
    """Reject retired/unknown names (the reactive controller's options were removed)."""
    unknown = set(params) - {f.name for f in fields(ObstacleConfig)} - set(allowed)
    if unknown:
        raise ValueError('Unsupported Obstacle parameters: ' + ', '.join(sorted(unknown))
                         + '. Use obstacle_sensors_v1.yaml; archived profiles need commit be3800d.')


def load_parameters(profile, overrides, allowed=()):
    """Load a saved ROS profile, then apply explicit key=value overrides."""
    params = {}
    if profile:
        params.update(yaml.safe_load(Path(profile).read_text())[
            'obstacle_strategy']['ros__parameters'] or {})
    for item in overrides:
        key, value = item.split('=', 1)
        params[key] = yaml.safe_load(value)
    validate_parameters(params, allowed)
    return params


def fixed_values():
    """The fixed (non-parameter) values, for run manifests."""
    return {name: getattr(ObstacleConfig, name) for name, hint in ObstacleConfig.__annotations__.items()
            if get_origin(hint) is ClassVar}


def config_with(**values):
    """ObstacleConfig with parameters set normally and fixed values overridden on this instance."""
    names = {f.name for f in fields(ObstacleConfig)}
    cfg = ObstacleConfig(**{k: v for k, v in values.items() if k in names})
    for name, value in values.items():
        if name not in names:
            if name not in fixed_values():
                raise TypeError(f'unknown Obstacle setting: {name}')
            setattr(cfg, name, value)
    return cfg

