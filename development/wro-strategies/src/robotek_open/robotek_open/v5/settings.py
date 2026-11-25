"""ROS parameters of the Open v5 node: the mission's own plus the node's and the camera's."""
from dataclasses import asdict

from .mission import Params

OPERATION = {
    'telemetry_path': '', 'auto_start': True, 'shutdown_on_done': True, 'done_hold': 35.0,
    'scan_max_age': 0.0, 'imu_max_age': 0.0, 'telemetry_sync_seconds': 0.0,
}
# Camera colours (OpenCV HSV: h_min, h_max, s_min, v_min; h_min > h_max wraps through red).
VISION = {
    'direction_confirmations': 5,
    'vision_blue_h_min': 90, 'vision_blue_h_max': 135, 'vision_blue_s_min': 60, 'vision_blue_v_min': 60,
    'vision_orange_h_min': 5, 'vision_orange_h_max': 28, 'vision_orange_s_min': 60, 'vision_orange_v_min': 60,
    'vision_floor_mask': False, 'vision_wall_v_max': 40, 'vision_wall_min_rows': 8,
    'vision_line_contrast': 0, 'vision_line_tint': 8,
}
PARAMETERS = {**asdict(Params()), **OPERATION, **VISION}


def validate_parameters(params, allowed=()):
    """Reject names the v5 node does not know (typos, or v4 parameters)."""
    unknown = set(params) - set(PARAMETERS) - set(allowed)
    if unknown:
        raise ValueError('Unsupported Open v5 parameters: ' + ', '.join(sorted(unknown))
                         + '. Use src/robotek_open/config/open_v5.yaml (Open v4 and older were removed).')
