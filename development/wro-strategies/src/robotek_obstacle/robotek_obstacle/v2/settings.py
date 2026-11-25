"""Parameters of the Obstacle v2 mission (12 ROS parameters, the rest are constants)."""
from dataclasses import dataclass, fields


@dataclass
class Params:
    cruise_speed: float = 0.35      # m/s on a clear lane
    pillar_speed: float = 0.30      # m/s while passing a sign or changing lane
    finish_speed: float = 0.15      # m/s on the last metres and the stop
    pillar_clearance: float = 0.18  # m from the sign box to the car's side
    pillar_lookahead: float = 1.80  # m ahead to start the side change
    steer_kp: float = 1.5           # rad of steer per rad of heading error to the planned line
    steer_kd: float = 0.2           # gyro damping
    steer_limit: float = 0.307      # rad, the real car after per-side compensation (17.6 deg)
    stop_progress: float = 24.7     # track units: 3 laps + 0.7 into the start straight
    park: float = 0.0               # 1: park in the lot after the three laps (rounds with the lot)
    park_after: float = 24.0        # track units driven before parking (3 laps; 0 in parking-only tests)
    park_speed: float = 0.06        # m/s while manoeuvring in the lot
    park_margin: float = 0.015      # m kept from the limits and the wall by the parking search
    scan_max_age: float = 0.35      # s; older LiDAR brakes
    imu_max_age: float = 0.20       # s; older gyro brakes


def validate(params):
    known = {f.name for f in fields(Params)}
    unknown = set(params) - known
    if unknown:
        raise ValueError('Unsupported Obstacle v2 parameters: ' + ', '.join(sorted(unknown)))
    return {k: float(v) for k, v in params.items()}


def make(params=None):
    values = validate(params or {})
    return Params(**values)
