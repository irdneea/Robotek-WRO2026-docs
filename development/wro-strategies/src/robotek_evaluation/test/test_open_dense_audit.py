"""Regression for sections present in audit poses but absent at telemetry rate."""
import csv
import json
from robotek_evaluation.open_round_report import add_rule_judge, scoring_pose_rows


def test_dense_audit_recovers_a_short_corner_without_changing_score_rules(tmp_path):
    centers = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]
    rows=[]
    for i in range(61):
        x,y=centers[i%8] if i<24 else centers[0]
        rows.append(dict(sim_time=i,wall_time=i,x_gt=x,y_gt=y,yaw_gt=0,
                         steer_actual=0,steer_right_actual=0,state='DONE' if i>=24 else 'FOLLOW'))
    events=[dict(event='start',sim_time=0,wall_time=0),dict(event='done',sim_time=24,wall_time=24)]
    (tmp_path/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    (tmp_path/'manifest.json').write_text(json.dumps({'direction':'ccw'}))
    sparse=[r for i,r in enumerate(rows) if i!=3]
    def write(name,data):
        with (tmp_path/name).open('w') as stream:
            w=csv.DictWriter(stream,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    write('telemetry.csv',sparse)
    low_rate=add_rule_judge(tmp_path,{'points_official':None}, {})
    assert low_rate['points_estimated']==18
    assert low_rate['rule_judge']['pose_source']=='telemetry.csv'
    write('audit_pose.csv',[{k:v for k,v in r.items() if k!='state'} for r in rows])
    dense=add_rule_judge(tmp_path,{'points_official':None}, {})
    assert dense['points_estimated']==30
    assert dense['points_official'] is None
    assert dense['rule_judge']['pose_source']=='audit_pose.csv'
    assert dense['rule_judge']['time_from_start_sim_seconds']==24
    assert len(dense['rule_judge']['lap_splits'])==3
    assert dense['rule_judge']['stop_hold_sim_seconds']==35


def test_incomplete_audit_retains_full_telemetry_and_done_event_sets_state(tmp_path):
    def write(name,rows):
        with (tmp_path/name).open('w') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    pose=dict(sim_time=1,wall_time=1,x_gt=0,y_gt=-1,yaw_gt=0,steer_actual=0,steer_right_actual=0)
    telemetry=[dict(pose,state='FOLLOW'),dict(pose,sim_time=2,wall_time=2,state='DONE')]
    write('audit_pose.csv',[pose])
    rows,source=scoring_pose_rows(tmp_path,telemetry,[])
    assert rows is telemetry and source=='telemetry.csv'
    write('audit_pose.csv',[pose,dict(pose,sim_time=1.95,wall_time=1.95)])
    rows,source=scoring_pose_rows(tmp_path,telemetry,[dict(event='done',sim_time=1.9)])
    assert source=='audit_pose.csv'
    assert [r['state'] for r in rows]==['FOLLOW','DONE']
