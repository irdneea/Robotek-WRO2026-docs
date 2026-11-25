"""Prepare the Open run directory, source snapshot, world and launch command."""

from dataclasses import asdict
import datetime
import inspect
import json
import math
from pathlib import Path
import re
import shutil

import yaml

from robotek_common import lidar_odometry
from robotek_open import open_constants
from robotek_open.open_constants import HARDWARE, SENSORS, LAPS, CONTROL_RATE, DISTANCE_MODEL_ACCEL
from .open_field_geometry import field_geometry
from robotek_open.open_profile import load_parameters


def resolved_v5(direction, params):
    """Mission parameters, node parameters and the constants of the v5 mission, for the run manifest."""
    from robotek_open.v5 import mission
    from robotek_open.v5.settings import PARAMETERS
    constants = {k: v for k, v in vars(mission).items() if k.isupper() and isinstance(v, (int, float, tuple))}
    return ({**PARAMETERS, **params, 'direction': direction} | constants | asdict(HARDWARE) | asdict(SENSORS)
            | {'laps': LAPS, 'control_rate': CONTROL_RATE, 'distance_model_accel': DISTANCE_MODEL_ACCEL})


def prepare_experiment(args, root):
    """Return the evidence directory and launch command for one attempt."""
    params = load_parameters(args.params_file, args.param)
    configured_direction = params.pop('direction', args.direction)
    controller_direction = args.controller_direction or configured_direction
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = root / 'docs' / 'open-challenge-runs' / (stamp + '-' + args.name)
    directory.mkdir(parents=True)
    snapshot = directory / 'source'
    snapshot.mkdir()
    world = (args.world.resolve() if args.world else
             root / 'install/robotek_gazebo/share/robotek_gazebo/worlds/robotek_open_field.sdf')
    geometry = field_geometry(world)
    shutil.copyfile(world, snapshot / 'world.sdf')
    # Audit: contact sensors on the walls (loaded with the world, unlike sensors of
    # the robot, which is spawned later and is not picked up by the Contact system).
    text = (snapshot / 'world.sdf').read_text()
    if 'gz-sim-contact-system' not in text:
        import re as _re
        plugin = ('<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>\n')
        head, sep, tail = text.partition('<world')
        world_tag_end = tail.index('>') + 1
        text = head + sep + tail[:world_tag_end] + '\n    ' + plugin + tail[world_tag_end:]
        walls = _re.findall(r'<collision name="(wall_(?:ext|int)_[a-z]+_col)"', text)
        if walls and '<link name="field">' in text:
            sensor = ('<sensor name="wall_contact" type="contact"><contact>'
                      + ''.join('<collision>%s</collision>' % w for w in walls)
                      + '<topic>/audit/robot_contacts</topic></contact>'
                      '<always_on>1</always_on><update_rate>100</update_rate></sensor>')
            text = text.replace('<link name="field">', '<link name="field">' + sensor, 1)
        (snapshot / 'world.sdf').write_text(text)
    if args.real_time_factor is not None:
        text = (snapshot / 'world.sdf').read_text()
        start = text.index('<physics')
        end = text.index('</physics>', start)
        block = re.sub(r'<real_time_factor>[^<]*</real_time_factor>',
                       '<real_time_factor>%g</real_time_factor>' % args.real_time_factor, text[start:end])
        (snapshot / 'world.sdf').write_text(text[:start] + block + text[end:])
    package = Path(inspect.getfile(open_constants)).parent
    for module in package.glob('open_*.py'):
        shutil.copyfile(module, snapshot / module.name)
    for module in (package / 'v5').glob('[!_]*.py'):
        shutil.copyfile(module, snapshot / ('v5_' + module.name))
    for module in Path(inspect.getfile(lidar_odometry)).parent.glob('[!_]*.py'):
        shutil.copyfile(module, snapshot / module.name)
    vehicle = root / 'install/robotek_description/share/robotek_description/urdf/robotek.urdf.xacro'
    if vehicle.exists():
        shutil.copyfile(vehicle, snapshot / vehicle.name)
    if args.params_file:
        shutil.copyfile(args.params_file, snapshot / 'profile.yaml')
    params['telemetry_path'] = str(directory / 'telemetry.csv')
    (directory / 'params.yaml').write_text(yaml.safe_dump({
        'open_strategy': {'ros__parameters': params},
    }))
    command = [
        'ros2', 'launch', 'robotek_bringup', 'open_challenge.launch.py',
        'gui:=' + str(not args.no_gui).lower(),
        'direction:=' + controller_direction,
        'world:=' + str(snapshot / 'world.sdf'),
        'params_file:=' + str(directory / 'params.yaml'),
        'audit_dir:=' + str(directory),
        'spawn_x:=' + str(args.spawn_x), 'spawn_y:=' + str(args.spawn_y),
        'rviz:=' + str(args.rviz).lower(),
        'ackermann_velocity_limit:=' + str(args.ackermann_velocity_limit),
        'ackermann_steer_p_gain:=' + str(args.ackermann_steer_p_gain),
        'strategy:=v5',
    ]
    spawn_yaw = args.spawn_yaw if args.spawn_yaw is not None else (
        math.pi if args.direction == 'cw' else 0.0
    )
    command.append('spawn_yaw:=' + str(spawn_yaw))
    if not any(item.startswith('real_car:=') for item in args.launch_arg):
        command.append('real_car:=true')   # the launch default, written so the manifest records it
    command += args.launch_arg
    manifest = {
        'command': command, 'direction': args.direction, 'parameters': params,
        'field_geometry': geometry, 'world_source': str(world),
        'started_utc': stamp,
        'strategy': 'v5',
        'resolved_config': resolved_v5(controller_direction, params),
        'ackermann_velocity_limit': args.ackermann_velocity_limit,
        'ackermann_steer_p_gain': args.ackermann_steer_p_gain,
        'launch_args': args.launch_arg,
        'gui': not args.no_gui,
        'honest': True,
        'real_time_factor': args.real_time_factor,
        'spawn': {'x': args.spawn_x, 'y': args.spawn_y, 'yaw': spawn_yaw},
        'sampling': 'CSV 10 Hz simulation-clock control timer; raw lidar scans with timestamps',
        'measurement': (
            'Lap milestones use turn counts; ground-truth winding checks progress. '
            'Geometric body clearance approximates the wall bounds read from the saved SDF.'
        ),
    }
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return directory, command
