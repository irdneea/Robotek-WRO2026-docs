"""Offline three-lap and traffic-rule checks from saved simulation evidence."""
import csv
import json
import math
from . import contact_log
from .rule_judge import JUDGE_VERSION, standard_validation, wall_sensor_present
from .obstacle_audit_geometry import (box_projection, collision_polygons, polygon_distance, quat_from_yaw,
                                      quat_multiply, quat_rotate, rectangle, tilt_degrees)

CIRCLE_RADIUS = .0425   # 85 mm evaluation circle (rules 13.15)
MOVED_M = .005          # internal: displacement treated as "moved" for 1.6/1.4
TILTED_DEG = 10.        # internal: tilt treated as "moved"
KNOCKED_DEG = 45.       # internal: tilt treated as knocked down
PILLAR_MARGIN_M = .03   # internal: profile-selection margin, not a rule


def section(x,y):
    if y<-.5:
        return 7 if x<-.5 else (1 if x>.5 else 0)
    if y>.5:
        return 5 if x<-.5 else (3 if x>.5 else 4)
    return 6 if x<0 else 2


def pillar_world_poses(frame):
    """World (x, y, quaternion, has_full_rotation) per pillar from one pillars-gt.jsonl frame."""
    poses=frame['poses']; parent=next((p for p in poses if p['name']=='traffic_signs'),None)
    if parent is None: return {}
    qp=tuple(parent['q']) if 'q' in parent else quat_from_yaw(parent['yaw'])
    result={}
    for p in poses:
        name=p['name'].split('/')[-1]
        if not name.startswith('sign_'): continue
        q=quat_multiply(qp,tuple(p['q']) if 'q' in p else quat_from_yaw(p['yaw']))
        dx,dy,_=quat_rotate(qp,(p['x'],p['y'],p['z']))
        result[name]=(parent['x']+dx,parent['y']+dy,q,'q' in p)
    return result


def pillar_outside_circle(frame,pillars):
    """Name of the first pillar whose ground projection leaves its 85 mm circle, else None."""
    seats={p['name']:p for p in pillars}
    for name,(x,y,q,_) in pillar_world_poses(frame).items():
        seat=seats.get(name)
        if seat and max(math.hypot(vx-seat['x'],vy-seat['y']) for vx,vy in box_projection(x,y,q))>CIRCLE_RADIUS:
            return name
    return None


def summarize_full(directory,manifest):
    rows=list(csv.DictReader((directory/'telemetry.csv').open())) if (directory/'telemetry.csv').exists() else []
    events=[json.loads(s) for s in (directory/'events.jsonl').read_text().splitlines()] if (directory/'events.jsonl').exists() else []
    start=next((e for e in events if e['event']=='start'),None)
    done=next((e for e in events if e['event']=='done'),None)
    valid=[r for r in rows if all(math.isfinite(float(r[k])) for k in ('x_gt','y_gt','yaw_gt'))]
    sign=1 if manifest['direction']=='ccw' else -1
    pillars=manifest['pillars']; armed={p['name']:False for p in pillars}; span={}; crossings=[]
    parking=bool(manifest.get('parking_lot'))
    visits=[]; laps=[]; distances=[]; legal_stop=None; fault=None
    last=0; transitions=0; lap_pending=False
    for r in valid:
        shapes=list(collision_polygons(r).values()); vertices=sum(shapes,[])
        x,y=float(r['x_gt']),float(r['y_gt']); sect=section(x,y)
        if sect==(last+sign)%8:
            transitions+=1; last=sect
            visits.append(dict(section=sect,sim_time=float(r['sim_time']),wall_time=float(r['wall_time'])))
            if transitions%8==0: lap_pending=True
        if lap_pending and all(-.5<=vx<=.5 and -1.5<=vy<=-.5 for vx,vy in vertices):
            laps.append(dict(lap=len(laps)+1,sim_time=float(r['sim_time']),wall_time=float(r['wall_time'])))
            lap_pending=False
        wall=min(min(polygon_distance(s,rectangle(0,0,0,.5,.5)) for s in shapes),min(1.5-max(abs(vx),abs(vy)) for vx,vy in vertices))
        row_pillar=math.inf
        for p in pillars:
            pp=rectangle(p['x'],p['y'],0,.025,.025)
            row_pillar=min(row_pillar,min(polygon_distance(s,pp) for s in shapes))
            # CCW tangents: east on bottom, north on right, west on top, south on left.
            tx,ty={'bottom':(1,0),'right':(0,1),'top':(-1,0),'left':(0,-1)}[p['side']]
            tx*=sign; ty*=sign; nx,ny=-ty,tx
            # Car near this pillar's radius line, anywhere across its corridor.
            own_side=(abs(x-p['x'])<.6 and y*math.copysign(1,p['y'])>=.45) if p['side'] in ('bottom','top') else (abs(y-p['y'])<.6 and x*math.copysign(1,p['x'])>=.45)
            # With the parking lot, the signs may be passed on any side once the three laps are done.
            if not own_side or (parking and len(laps)>=3): continue
            progress=[tx*(vx-p['x'])+ty*(vy-p['y']) for vx,vy in vertices]
            lateral=[nx*(vx-p['x'])+ny*(vy-p['y']) for vx,vy in vertices]
            if max(progress)<0: armed[p['name']]=True; span[p['name']]=None
            if armed[p['name']] and min(progress)<=0<=max(progress):
                # Where the footprint cuts the radius line (lateral interval), per sample.
                cuts=[]
                for shape in shapes:
                    for (ax,ay),(bx,by) in zip(shape,shape[1:]+shape[:1]):
                        pa=tx*(ax-p['x'])+ty*(ay-p['y']); pb=tx*(bx-p['x'])+ty*(by-p['y'])
                        if (pa<=0<=pb or pb<=0<=pa) and pa!=pb:
                            la=nx*(ax-p['x'])+ny*(ay-p['y']); lb=nx*(bx-p['x'])+ny*(by-p['y'])
                            cuts.append(la+(lb-la)*pa/(pa-pb))
                if cuts:
                    lo,hi=span[p['name']] or (math.inf,-math.inf)
                    span[p['name']]=(min(lo,min(cuts)),max(hi,max(cuts)))
            if armed[p['name']] and min(progress)>0:
                lo,hi=span[p['name']] or (min(lateral),max(lateral))
                clearance=-hi-.025 if p['color']=='red' else lo-.025
                crossing=dict(pillar=p['name'],color=p['color'],lap=len(laps)+1,sim_time=float(r['sim_time']),
                              wall_time=float(r['wall_time']),correct_side=clearance>0,side_clearance_m=clearance,
                              line_cut_lateral_m=[lo,hi])
                crossings.append(crossing); armed[p['name']]=False
                if clearance<=0 and fault is None: fault=dict(reason='wrong_side',**crossing)
        # Parking is done against the wall (2.6 cm a side in the lot): the wall margin is a lap check.
        distances.append((float(r['sim_time']),row_pillar,wall if not (parking and len(laps)>=3) else math.inf))
        if r['state']=='DONE':
            legal_stop=all(-.5<=vx<=.5 and -1.5<=vy<=-.5 for vx,vy in vertices)
    # Compose link-local poses with the model pose (model follows canonical link).
    motion={p['name']:[] for p in pillars}; tilt_evaluated=False
    gt=directory/'pillars-gt.jsonl'
    if gt.exists():
        for line in gt.read_text().splitlines():
            frame=json.loads(line)
            for name,(wx,wy,q,has_q) in pillar_world_poses(frame).items():
                if name not in motion: continue
                tilt_evaluated=tilt_evaluated or has_q
                seat=next(p for p in pillars if p['name']==name)
                maximum=max(math.hypot(vx-seat['x'],vy-seat['y']) for vx,vy in box_projection(wx,wy,q))
                motion[name].append(dict(sim_time=frame['sim_time'],x=wx,y=wy,tilt_deg=tilt_degrees(q),max_projection_radius_m=maximum))
    moved_out=[]
    for name,poses in motion.items():
        outside=next((p for p in poses if p['max_projection_radius_m']>CIRCLE_RADIUS),None)
        if outside: moved_out.append(dict(pillar=name,**outside))
    if moved_out:
        earliest=min(moved_out,key=lambda p:p['sim_time'])
        if fault is None or earliest['sim_time']<fault['sim_time']: fault=dict(reason='pillar_outside_circle',**earliest)
    cutoff=fault['sim_time'] if fault else math.inf
    if fault:
        laps=[p for p in laps if p['sim_time']<cutoff]
        visits=[v for v in visits if v['sim_time']<cutoff]
        # The faulting crossing is kept; anything after the round ended does not count.
        crossings=[c for c in crossings if c['sim_time']<=cutoff]
        moved_out=[m for m in moved_out if m['sim_time']<=cutoff]
    in_round=[d for d in distances if d[0]<=cutoff]
    min_wall=min((d[2] for d in in_round),default=math.inf); min_pillar=min((d[1] for d in in_round),default=math.inf)
    contacts_path=directory/'contacts.jsonl'; contact_evaluated=contacts_path.exists()
    contacts=contact_log.read(contacts_path) if contact_evaluated else []
    contacts=[c for c in contacts if c['sim_time']<=cutoff]
    movement=[]; statuses={}
    for p in pillars:
        poses=[q for q in motion[p['name']] if q['sim_time']<=cutoff]
        touches=[c for c in contacts if c['pillar']==p['name']]
        entry=dict(pillar=p['name'],color=p['color'],samples=len(poses),contact_messages=contact_log.message_count(touches),
                   first_contact_sim_time=touches[0]['sim_time'] if touches else None)
        if poses:
            first=poses[0]
            entry.update(max_horizontal_motion_m=max(math.hypot(q['x']-first['x'],q['y']-first['y']) for q in poses),
                         max_tilt_deg=max(q['tilt_deg'] for q in poses),
                         max_projection_radius_m=max(q['max_projection_radius_m'] for q in poses))
            if entry['max_projection_radius_m']>CIRCLE_RADIUS: status='outside_circle'
            elif entry['max_tilt_deg']>KNOCKED_DEG: status='knocked_down_inside'
            elif entry['max_horizontal_motion_m']>MOVED_M or entry['max_tilt_deg']>TILTED_DEG: status='moved_inside'
            elif touches: status='touched_not_moved'
            else: status='untouched' if contact_evaluated else 'not_moved_contact_unknown'
        else:
            status='no_ground_truth'
        entry['status']=status; statuses[p['name']]=status; movement.append(entry)
    any_moved=any(v in ('outside_circle','knocked_down_inside','moved_inside') for v in statuses.values())
    end=done or next((e for e in reversed(events) if e['event'] in ('timeout','direction_fault')),None)
    if fault: end=dict(sim_time=fault['sim_time'],wall_time=next(float(r['wall_time']) for r in valid if float(r['sim_time'])>=fault['sim_time']))
    if end is None and rows: end={k:float(rows[-1][k]) for k in ('sim_time','wall_time')}
    splits=[]; previous=start
    for lap in laps:
        if previous:
            splits.append(dict(lap=lap['lap'],sim_seconds=lap['sim_time']-previous['sim_time'],wall_seconds=lap['wall_time']-previous['wall_time'],cumulative_sim_seconds=lap['sim_time']-start['sim_time']))
        previous=lap
    stationary=[] if done is None else [r for r in valid if float(r['sim_time'])>=done['sim_time']+.5]
    drift=max((math.hypot(float(r['x_gt'])-float(stationary[0]['x_gt']),float(r['y_gt'])-float(stationary[0]['y_gt'])) for r in stationary),default=None)
    hold=None if done is None or not rows else float(rows[-1]['sim_time'])-done['sim_time']
    # Drift while stopped: the rules only require stopping in the start sector, and 2.5 mm of
    # simulation creep was costing the 3 stop points (22 Oct 2026 decision, docs/obstacle-reimpl-v2.md).
    stop_valid=bool(done and legal_stop and hold is not None and hold>=30 and drift is not None and drift<.02)
    complete=bool(done and len(laps)>=3 and not fault and legal_stop)
    counts={p['name']:sum(c['pillar']==p['name'] and c['correct_side'] for c in crossings) for p in pillars}  # crossings already cut at fault
    all_signs=all(count>=3 for count in counts.values())
    sensors_complete=all(motion[p['name']] for p in pillars)
    times={k+'_seconds':end[k]-start[k] for k in ('sim_time','wall_time')} if start and end else None
    valid_round=bool(complete and all_signs and sensors_complete and stop_valid and times and times['sim_time_seconds']<=180 and min_wall>.01)
    estimated=min(24,len(visits))+min(3,len(laps))+(3 if complete and stop_valid else 0)
    # 1.6/1.7 after three laps, 1.4/1.5 with at least one lap; any displacement counts as moved (internal, conservative).
    sign_bonus=0 if not sensors_complete else ((8 if any_moved else 10) if len(laps)>=3 else ((2 if any_moved else 4) if len(laps)>=1 else 0))
    breakdown={'1.1_sections':min(24,len(visits)),'1.2_laps':min(3,len(laps)),'1.3_stop_in_finish':3 if complete and stop_valid else 0,
               '1.4-1.7_traffic_signs':sign_bonus,'1.8_parking':None}
    by_lap={}
    for c in crossings: by_lap.setdefault(str(c['lap']),[]).append({k:c[k] for k in ('pillar','color','correct_side','side_clearance_m','sim_time')})
    if fault: verdict='round_ended_'+fault['reason']
    elif not complete: verdict='incomplete'
    else: verdict='three_laps_signs_moved_bonus_8' if any_moved else 'three_laps_signs_not_moved_bonus_10'
    report=dict(test_scope='three_laps_no_parking',completed=complete,full_round_validated=valid_round,
                official_points=None,points_estimated=estimated+sign_bonus,points_driving_estimated=estimated,
                points_signs_provisional=sign_bonus,bonus_provisional=sign_bonus,parking_evaluated=False,
                laps_completed=len(laps),lap_splits=splits,timings=times,section_visits=visits,rule_fault=fault,
                radius_crossings=crossings,crossings_by_lap=by_lap,correct_crossings_per_pillar=counts,all_pillars_passed_three_times=all_signs,
                verdict=verdict,points_breakdown_estimated=breakdown,pillar_status=statuses,any_sign_moved=any_moved,
                pillar_movements=movement,pillars_outside_circle=moved_out,ground_truth_pillars_complete=sensors_complete,
                contact_evaluated=contact_evaluated,tilt_evaluated=tilt_evaluated,
                internal_thresholds=dict(moved_m=MOVED_M,tilted_deg=TILTED_DEG,knocked_deg=KNOCKED_DEG,pillar_margin_m=PILLAR_MARGIN_M),
                internal_pillar_margin_ok=min_pillar>=PILLAR_MARGIN_M,
                min_sampled_wall_clearance_m=None if not valid else min_wall,min_sampled_pillar_clearance_m=None if not valid else min_pillar,
                stop_in_start_section=legal_stop,stop_hold_sim_seconds=hold,stop_max_displacement_m=drift,stop_validated=stop_valid,
                max_steer_degrees=max((abs(math.degrees(float(r[k]))) for r in valid for k in ('steer_actual','steer_right_actual')),default=None),
                selected_direction=rows[-1].get('selected_direction') if rows else None,samples=len(rows),
                limitations=['Offline sampled audit: clearances at telemetry rate; contacts from Gazebo sensors only when contact_evaluated.',
                             'Moved/tilted thresholds are internal: the rules do not define a millimetre threshold for "moved".',
                             'No parking or initial parking bonus; simplified start; not a complete 62-point event.',
                             'Points estimated from ordered section visits, not official scoring; pillar bonuses provisional.'])
    # Standard blocks shared with the Open judge (rules vs internal validation).
    faults=[]
    if fault:
        faults.append(dict(rule={'wrong_side':'9.24.5','pillar_outside_circle':'9.24.6'}.get(fault['reason'],'9.24'),
                           fault=fault['reason'],sim_time=fault['sim_time'],pillar=fault.get('pillar')))
    end_info=None
    if times and end:
        end_info=dict(reason=('round_ended_'+fault['reason']) if fault else ('stopped_after_three_laps' if done else 'end_of_recording'),
                      sim_time=end['sim_time'])
    walls_evaluated=wall_sensor_present(directory)
    wall_contacts=[c for c in contacts if c.get('kind') in ('outer_wall','inner_wall')] if walls_evaluated else []
    judge=dict(version=JUDGE_VERSION,challenge='obstacle_no_parking',max_points=40,points=report['points_estimated'],
               breakdown=report['points_breakdown_estimated'],faults=faults,round_end=end_info,
               time_from_start_sim_seconds=(times or {}).get('sim_time_seconds'),
               time_from_start_wall_seconds=(times or {}).get('wall_time_seconds'),
               lap_splits=splits,contact_evaluated=contact_evaluated,wall_contact_evaluated=walls_evaluated,
               notes=['Max 62 with parking; parking (1.8) not evaluated, so the scope maximum is 40.',
                      'Touching walls is allowed in Obstacle if they do not move (static in simulation).'])
    report['rule_judge']=judge
    if parking:
        _add_parking(report,judge,directory,manifest)
    report['validation']=standard_validation(
        judge,dict(wall=None if not valid else min_wall,pillar=None if not valid else min_pillar),
        contact_evaluated,[c for c in contacts]+wall_contacts if contact_evaluated else None,
        hold if stop_valid or hold else None,report['max_steer_degrees'])
    return report


def _add_parking(report,judge,directory,manifest):
    """Parking points (1.8.2/1.8.3) once the three laps are complete, from the parking judge."""
    from .obstacle_parking_report import summarize_parking
    park=summarize_parking(directory,manifest)
    points=park['points_estimated'] if report['completed'] else 0
    report.update(test_scope='three_laps_and_parking',parking_evaluated=True,parking=park,
                  points_estimated=report['points_estimated']+points)
    report['points_breakdown_estimated']['1.8_parking']=points
    judge.update(challenge='obstacle_with_parking',max_points=55,points=report['points_estimated'],
                 breakdown=report['points_breakdown_estimated'],
                 notes=['Max 62: the start-in-the-lot bonus (1.8.1, 7 points) is out of scope, so 55 here.',
                        'Touching walls is allowed in Obstacle if they do not move (static in simulation).',
                        'After the three laps the signs may be passed on either side (parking phase).'])
