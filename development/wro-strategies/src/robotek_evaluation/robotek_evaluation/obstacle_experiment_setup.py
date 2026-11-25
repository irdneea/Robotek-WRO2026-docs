"""Prepare an Obstacle round: regulation world, audit sensors, parameters, snapshot, command."""
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import shutil
import xml.etree.ElementTree as ET

import yaml

from robotek_common.vehicle import RULES_LENGTH
from robotek_obstacle.obstacle_config import fixed_values, load_parameters

NODE_PARAMETERS = ('telemetry_path', 'done_hold', 'direction', 'auto_start')


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def add_contact_audit(world,*models):
    # Audit only: one contact sensor per pillar, all on one topic for the recorder.
    ET.SubElement(world,'plugin',filename='gz-sim-contact-system',name='gz::sim::systems::Contact')
    # Walls: one sensor on the static field link (static walls publish only on contact).
    field=world.find("model[@name='game_field']/link[@name='field']")
    if field is not None:
        walls=[c.attrib['name'] for c in field.findall('collision') if c.attrib.get('name','').startswith('wall_')]
        sensor=ET.SubElement(field,'sensor',name='wall_contact',type='contact')
        contact=ET.SubElement(sensor,'contact')
        for w in walls: ET.SubElement(contact,'collision').text=w
        ET.SubElement(contact,'topic').text='/audit/robot_contacts'
        for key,val in dict(always_on='1',update_rate='100').items(): ET.SubElement(sensor,key).text=val
    for link in (l for model in models for l in model.findall('link')):
        sensor=ET.SubElement(link,'sensor',name='contact',type='contact')
        contact=ET.SubElement(sensor,'contact')
        ET.SubElement(contact,'collision').text=link.find('collision').attrib['name']
        ET.SubElement(contact,'topic').text='/obstacle/contacts'  # gz-sim reads the topic here, not under <sensor>
        for key,val in dict(always_on='1',update_rate='100').items():
            ET.SubElement(sensor,key).text=val

# Rules fig. 3 / 8c: per straight, seats at both section ends and the middle
# (along -.5, 0, +.5 m), 400 or 600 mm from the inner wall. Cards are read with the
# inner wall on top; card "right" is the CCW tangent. Two-sign cards always use
# both ends. The exact 36-card list is approximated from the figure (see docs).
SECTIONS={'bottom':((1,0),(0,-1)),'right':((0,1),(1,0)),'top':((-1,0),(0,1)),'left':((0,-1),(-1,0))}
CLOCKWISE=['bottom','left','top','right']
SINGLE_CARDS=[(pos,row,color) for row in (.4,.6) for pos in (-.5,0.,.5) for color in ('green','red')]
DOUBLE_CARDS=[((-.5,lrow,lcol),(.5,rrow,rcol)) for lrow in (.4,.6) for rrow in (.4,.6)
              for lcol in ('green','red') for rcol in ('green','red')]

def regulation_signs(seed,parking=False):
    """Signs of a regulation layout. With the parking lot, the signs of the start section
    (the bottom straight) move to the row next to the inner wall (rules, randomisation step 5)."""
    rng=random.Random(seed)
    single=rng.choice(CLOCKWISE); color=rng.choice(['green','red'])
    plan={single:[(0.,.6,color)]}  # the removed card 9/10 is the middle, outer-row seat
    deck=[[c] for c in SINGLE_CARDS if not (c[0]==0. and c[1]==.6)]+[list(c) for c in DOUBLE_CARDS]
    rng.shuffle(deck)
    start=CLOCKWISE.index(single)
    for k in range(1,4):
        plan[CLOCKWISE[(start+k)%4]]=deck.pop()
    signs=[]
    for side,cards in plan.items():
        (tx,ty),(nx,ny)=SECTIONS[side]
        for along,row,col in cards:
            if parking and side=='bottom': row=.4
            lateral=.5+row  # distance from the field centre along the outward normal
            signs.append(dict(color=col,x=round(tx*along+nx*lateral,3),y=round(ty*along+ny*lateral,3),side=side,
                              seat=dict(along_ccw_m=along,from_inner_wall_m=row)))
    counts={'red':0,'green':0}
    for sign in signs:
        counts[sign['color']]+=1; sign['name']=f"sign_{sign['color']}_{counts[sign['color']]}"
    return signs

def build_world(directory,seed,root,parking=False):
    """Regulation layout for this seed, with audit contact sensors and pillar pose publisher;
    ``parking`` adds the lot limits in the start section and moves its signs inward."""
    def parse(path):
        return ET.fromstring(re.sub(r'<!--.*?-->','',path.read_text(),flags=re.S))
    tree=parse(root/'src/robotek_gazebo/worlds/robotek_open_field.sdf'); world=tree.find('world'); world.set('name','robotek_obstacle_round')
    source=parse(root/'src/robotek_gazebo/worlds/robotek_game_field.sdf')
    model=copy.deepcopy(source.find("world/model[@name='traffic_signs']"))
    templates={c:copy.deepcopy(model.find(f"link[@name='sign_{c}_1']")) for c in ('red','green')}
    for link in model.findall('link'): model.remove(link)
    result=regulation_signs(seed,parking)
    for sign in result:
        link=copy.deepcopy(templates[sign['color']]); link.set('name',sign['name'])
        link.find('pose').text=f"{sign['x']} {sign['y']} 0.05 0 0 0"; model.append(link)
        sign['size_m']=[.05,.05,.1]
    plugin=ET.SubElement(model,'plugin',filename='gz-sim-pose-publisher-system',name='gz::sim::systems::PosePublisher')
    for key,val in dict(publish_model_pose='true',publish_link_pose='true',use_pose_vector_msg='true',update_frequency='20').items(): ET.SubElement(plugin,key).text=val
    lot=[_lot_model(world)] if parking else []
    add_contact_audit(world,model,*lot)
    world.append(model); ET.ElementTree(tree).write(directory/'world.sdf',encoding='unicode',xml_declaration=True)
    return result


# Parking lot by the rules: start section, CCW-downstream end of the bottom straight, one
# limit next to the section line (x = 0.5), 20 cm deep, 1.5 x robot length (vehicle.RULES_LENGTH, 0.245 m measured on the car).
PARKING_LOT = dict(x0=.48-1.5*RULES_LENGTH, x1=.48, y0=-1.5, y1=-1.3)   # 1.5 x the robot's length (rules)


def _lot_model(world):
    """The two magenta limits of the lot (200 x 20 x 100 mm) as a static model of the world."""
    model = ET.SubElement(world, 'model', name='parking_lot')
    ET.SubElement(model, 'static').text = 'true'
    lot = PARKING_LOT
    for name, x in (('parking_limit_a', lot['x0']-.01), ('parking_limit_b', lot['x1']+.01)):
        link = ET.SubElement(model, 'link', name=name)
        ET.SubElement(link, 'pose').text = f"{x} {(lot['y0']+lot['y1'])/2} 0.05 0 0 0"
        for kind in ('visual', 'collision'):
            element = ET.SubElement(link, kind, name=f'{name}_{kind}')
            ET.SubElement(ET.SubElement(element, 'geometry'), 'box')
            ET.SubElement(element.find('geometry/box'), 'size').text = '0.02 0.20 0.10'
            if kind == 'visual':
                material = ET.SubElement(element, 'material')
                for key in ('ambient', 'diffuse'):
                    ET.SubElement(material, key).text = '1 0 1 1'
    return model


def build_parking_world(directory, root):
    """Open field plus only the parking lot limits (magenta, 200 x 20 x 100 mm), audited."""
    def parse(path):
        return ET.fromstring(re.sub(r'<!--.*?-->', '', path.read_text(), flags=re.S))
    tree = parse(root/'src/robotek_gazebo/worlds/robotek_open_field.sdf')
    world = tree.find('world')
    world.set('name', 'robotek_parking')
    add_contact_audit(world, _lot_model(world))
    ET.ElementTree(tree).write(directory/'world.sdf', encoding='unicode', xml_declaration=True)
    return []


V1_PROFILE = 'src/robotek_obstacle/config/obstacle_sensors_v1.yaml'   # --strategy current
V2_PROFILE = 'src/robotek_obstacle/config/obstacle_v2.yaml'
V2_NODE_PARAMETERS = NODE_PARAMETERS + ('camera_hfov', 'camera_pitch', 'camera_yaw')


def _v2_parameters(profile, overrides, version='v2'):
    """Profile + key=value overrides for the v2/v3 node, checked against its settings.py."""
    from importlib import import_module
    validate = import_module(f'robotek_obstacle.{version}.settings').validate
    params = dict(yaml.safe_load(open(profile).read())['obstacle_strategy']['ros__parameters'] or {})
    for item in overrides:
        key, value = item.split('=', 1)
        params[key] = yaml.safe_load(value)
    validate({k: v for k, v in params.items() if k not in V2_NODE_PARAMETERS})
    return params


def prepare_round(args, directory, root):
    """World, parameters, source snapshot and launch command for one recorded round.

    ``args.strategy`` 'v2' runs robotek_obstacle/v2 (obstacle_strategy_v2); ``args.layout``
    'regulation-park' is the regulation layout with the parking lot (the car parks after the laps).
    """
    version = getattr(args, 'strategy', 'v3')
    v2 = version in ('v2', 'v3')        # the v2 family: v2 and v3 share node, profile and wiring
    with_lot = args.layout == 'regulation-park'
    if v2:
        default = str(root/V2_PROFILE).replace('obstacle_v2', f'obstacle_{version}')
        if args.profile and f'obstacle_{version}' not in Path(args.profile).name:
            raise SystemExit(f'--profile {args.profile} is not an obstacle_{version} profile '
                             '(obstacle_sensors_v1.yaml needs --strategy current)')
        profile = args.profile or default
        args.profile = profile
        params = _v2_parameters(profile, args.param, version)
        if with_lot or args.layout == 'parking':
            params['park'] = 1.0
        if args.layout == 'parking':
            params['park_after'] = 0.0
    else:
        args.profile = args.profile or str(root/V1_PROFILE)
        params = load_parameters(args.profile, args.param, allowed=NODE_PARAMETERS)
    params.update(telemetry_path=str(directory/'telemetry.csv'), direction='auto')
    parking = args.layout == 'parking'
    if parking and not v2:
        params['mode'] = 'park'
    (directory/'params.yaml').write_text(yaml.safe_dump(dict(obstacle_strategy=dict(ros__parameters=params))))
    pillars = (build_parking_world(directory, root) if parking
               else build_world(directory, args.seed, root, with_lot))
    if args.real_time_factor is not None:
        text = (directory/'world.sdf').read_text()
        a = text.index('<physics'); b = text.index('</physics>', a)
        text = text[:a]+re.sub(r'<real_time_factor>[^<]*</real_time_factor>',
                               '<real_time_factor>%g</real_time_factor>' % args.real_time_factor, text[a:b])+text[b:]
        (directory/'world.sdf').write_text(text)
    source = directory/'source'
    source.mkdir()
    files = (list((root/'src/robotek_obstacle/robotek_obstacle').glob('obstacle*.py'))
             + (list((root/'src/robotek_obstacle/robotek_obstacle'/version).glob('[!_]*.py')) if v2 else [])
             + list((root/'src/robotek_common/robotek_common').glob('[!_]*.py'))
             + [root/'src/robotek_description/urdf/robotek.urdf.xacro',
                root/'src/robotek_evaluation/tools/run_obstacle_gui_experiment.py',
                root/'src/robotek_bringup/launch/obstacle_challenge.launch.py'])
    hashes = {}
    for path in files:
        shutil.copy2(path, source/((path.parent.name + '_' if path.parent.name in ('v2', 'v3') else '')+path.name))
        hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if args.profile:
        shutil.copyfile(args.profile, source/'profile.yaml')
    sign = 1 if args.direction == 'ccw' else -1
    command = ['ros2', 'launch', 'robotek_bringup', 'obstacle_challenge.launch.py',
               f'gui:={str(not args.no_gui).lower()}', f'rviz:={str(not args.no_rviz).lower()}',
               f'spawn_x:={args.spawn_progress*sign}', f'world:={directory}/world.sdf',
               f'params_file:={directory}/params.yaml', f'audit_dir:={directory}',
               f'spawn_yaw:={0.0 if sign > 0 else math.pi}', 'ackermann_velocity_limit:=4.0',
               f'ackermann_steer_p_gain:={args.steer_p_gain}']+[f'strategy:=obstacle_strategy_{version}' if v2 else 'strategy:=obstacle_strategy']+(
               [] if any(a.startswith('real_car:=') for a in args.launch_arg) else ['real_car:=true'])+args.launch_arg
    manifest = dict(scope='parking' if parking else 'round', layout=args.layout,
                    parking_lot=PARKING_LOT if parking or with_lot else None,
                    strategy=version if v2 else 'current',
                    seed=None if parking else args.seed, pillars=pillars, name=args.name,
                    direction=args.direction, spawn_progress=args.spawn_progress, params=params,
                    fixed_values=None if v2 else fixed_values(),
                    profile=args.profile, command=command, source_sha256=hashes, gui=not args.no_gui,
                    rviz=not args.no_rviz, steer_p_gain=args.steer_p_gain, launch_args=args.launch_arg,
                    honest=True, real_time_factor=args.real_time_factor)
    return pillars, command, manifest
