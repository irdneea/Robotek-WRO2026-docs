"""Tunable parameters of the Obstacle mission.

Everything a human may want to change on the car is here, in one place, with its default. They are also ROS parameters
of the node, so any of them can be set at launch or from a YAML profile (see config/car_picam_park_round.yaml, the
profile used for the validated rounds). Fixed constants that are not meant to be tuned live next to the code that
uses them (mission.py, lot_exit.py, park_fixed.py).

Units: metres, seconds, radians. "Track units" are the lane's own measure: one unit per straight and one per corner,
eight per lap.
"""
from dataclasses import dataclass, fields


@dataclass
class Params:
    # --- Speeds -----------------------------------------------------------------------------------------------
    cruise_speed: float = 0.28      # m/s on a free lane. At 0.35 the lab car hit a sign on every seed; 0.28 did not
    pillar_speed: float = 0.30      # m/s while passing a sign or changing side
    finish_speed: float = 0.15      # m/s over the last metres and the stop
    front_speed: float = 0.20       # m/s cap while something is closer than front_distance ahead
    front_distance: float = 0.55    # m
    tight_speed: float = 0.15       # m/s in a corner planned with less clearance than tight_gap
    tight_gap: float = 0.07         # m; 0 turns the slow-down off
    known_speed_gain: float = 1.0   # cruise and pillar speed multiplier from lap 2, when every sign is known

    # --- Passing signs ----------------------------------------------------------------------------------------
    pillar_clearance: float = 0.18  # m from the sign's box to the side of the car when passing it
    pillar_lookahead: float = 1.80  # m ahead at which the car starts changing side for a sign
    unknown_offset: float = 0.0     # m away from a sign whose colour is not known yet (0 = stay in the lane's middle)
    lane_offset: float = 0.0        # if > 0, every sign of known colour is passed at plus or minus this offset

    # --- Steering law -----------------------------------------------------------------------------------------
    steer_kp: float = 1.5           # steering per radian of heading error to the planned line
    steer_kd: float = 0.2           # damping on the gyro's yaw rate
    steer_limit: float = 0.307      # rad, the largest real wheel angle of the car (17.6 degrees)
    preview_time: float = 0.0       # s; if > 0 the curvature feed-forward looks this much speed-times-time ahead

    # --- Corners ----------------------------------------------------------------------------------------------
    tracked_corners: float = 1.0    # 1: score corner lines by driving them in a simulation of the car (corner.py)
    corner_replan: float = 1.0      # 1: choose the corner line again when the signs change with the car inside it

    # --- Safety -----------------------------------------------------------------------------------------------
    steer_watch: float = 1.0        # 1: stop and centre the wheels when full lock gives no turn on the gyro
    guard_gap: float = 0.0          # m; if > 0, back off when the car's outline gets this close to a sign or wall
    recover_back: float = 0.5       # s of reverse at full lock in the front recover (the round profile uses 0.3)
    scan_max_age: float = 0.35      # s; an older LiDAR scan stops the car
    imu_max_age: float = 0.20       # s; an older gyro reading stops the car

    # --- Round ------------------------------------------------------------------------------------------------
    stop_progress: float = 24.7     # track units at which the round ends: three laps plus 0.7 into the start straight
    start_lot: float = 0.0          # 1: the car starts inside the parking lot and leaves it first (lot_exit.py)
    lot_exit_speed: float = 0.90    # m/s of the lot exit pulses (the round command uses 0.2)

    # --- Parking ----------------------------------------------------------------------------------------------
    park: float = 0.0               # 1: park in the lot after the three laps
    park_after: float = 24.0        # track units driven before parking starts (three laps)
    lot_laps: float = 1.0           # 1: the laps keep away from the lot's limits; 0: drive as if there were no lot
    park_mode: float = 0.0          # 0: the planned manoeuvre (park.py); 1: the fixed one closed on sensors (park_fixed.py)
    park_speed: float = 0.06        # m/s while manoeuvring in the lot (the motor floor makes it about 0.25)
    park_margin: float = 0.015      # m kept from the limits and the wall by the planned park
    park_fixed_ahead: float = 0.145  # m past the lot's far limit at which the fixed manoeuvre starts to reverse
    park_fixed_entry: float = 0.76  # rad of heading at which the entry arc ends (read from the gyro)
    park_fixed_margin: float = 0.012  # m kept from the limits and the wall by the fixed manoeuvre's guard
    park_fixed_roll: float = 0.012  # m the car is assumed to roll after a stop, until a real roll is measured
    park_fixed_roll_arc: float = 0.0  # the same for a stop at full lock (0 = use park_fixed_roll)
    park_fixed_partial: float = 0.0  # 1: stop after the entry arc and the straight into the lot, then the finishing pulses
    park_partial_back: float = 0.5  # s of extra straight reverse at the end of the partial park (the rear sensor stops it)
    park_pulse_speed: float = 0.2   # m/s of the finishing pulses (park_finish_steps)
    park_align_speed: float = 0.0   # m/s of the line-up before the entry; 0 = use park_speed
    park_fixed_sense: float = 0.0   # 1: place the lot from what the LiDAR sees (outer wall and limit plates)
    park_lot_length: float = 0.3675  # m between the inner faces of the limits: 1.5 times the car's 0.245 m
    park_lot_depth: float = 0.20    # m from the outer wall, fixed by the rules
    park_lot_end: float = 0.48      # m along the start straight to the far limit's inner face (CCW; mirrored in CW)


def validate(params):
    known = {f.name for f in fields(Params)}
    unknown = set(params) - known
    if unknown:
        raise ValueError('Unsupported Obstacle v3 parameters: ' + ', '.join(sorted(unknown)))
    return {k: float(v) for k, v in params.items()}


def make(params=None):
    values = validate(params or {})
    return Params(**values)
