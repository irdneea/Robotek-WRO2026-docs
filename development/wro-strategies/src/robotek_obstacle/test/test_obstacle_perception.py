import math
from types import SimpleNamespace
import cv2
import numpy as np
import pytest
from robotek_obstacle.obstacle_beam_planner import BeamPlanner
from robotek_obstacle.obstacle_config import config_with, validate_parameters
from robotek_obstacle.obstacle_field import make_seats
from robotek_obstacle.obstacle_mission import ObstacleMission
from robotek_obstacle.obstacle_perception import color_blocks, associate, scan_clusters


def test_color_wrap_and_floor_rejection():
    hsv=np.zeros((180,320,3),dtype=np.uint8)
    hsv[20:90,50:70]=[175,220,220]
    hsv[30:100,180:200]=[60,220,220]
    hsv[140:146,20:290]=[4,220,220]
    blocks=color_blocks(cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR))
    assert {b['color'] for b in blocks}=={'red','green'}
    assert len(blocks)==2
    assert next(b for b in blocks if b['color']=='red')['bearing']>0


def test_conflicting_colors_do_not_assign_one_lidar_object():
    clusters=[dict(x=.5,y=0.,points=5,diameter_m=.05)]
    blocks=[dict(color=c,bearing=0.,box=(1,1,10,30)) for c in ('red','green')]
    assert associate(blocks,clusters)==[]
    assert associate(blocks[:1],clusters)[0]['color']=='red'
    assert associate([dict(blocks[0],bearing=.4)],clusters)==[]


def test_short_lidar_object_distinguished_from_wall():
    scan=SimpleNamespace(range_min=.02,angle_min=-.2,angle_increment=.01,
                         ranges=[math.inf]*10+[.5]*10+[math.inf]*10+[1.]*30)
    objects=scan_clusters(scan)
    assert len(objects)==1
    assert .015<objects[0]['diameter_m']<.12


def test_wrong_side_while_straddling_the_radius_line():
    seat=dict(make_seats()[2],color='green')  # bottom straight, travel +x: green passes on the left
    t=seat['t']
    for lateral,wrong in ((.2,False),(-.2,True)):
        x,y=seat['x']-t[1]*lateral,seat['y']+t[0]*lateral
        assert bool(BeamPlanner.wrong_side(x,y,math.atan2(t[1],t[0]),[seat]))==wrong
    # Far before the line nothing is straddled.
    assert not BeamPlanner.wrong_side(seat['x']-.5,seat['y']-.2,0.,[seat])


def test_retired_reactive_parameters_are_rejected():
    validate_parameters({'plan_speed':.5})
    with pytest.raises(ValueError):
        validate_parameters({'cruise_speed':.35})


def test_calibration_then_lidar_or_camera_decides():
    mission=ObstacleMission(config_with(calibrate_seconds=.04))
    assert mission.step(0.,None,-math.inf,0.,0.,.01,0.)[2]=='CALIBRATE'
    for k in range(1,4):
        state=mission.step(.02*k,None,-math.inf,.02*k,0.,.01,0.)[2]
    assert state=='DETECT_DIRECTION' and abs(mission.gyro_bias-.01)<1e-12
    mission.lines.direction=-1  # camera lines say CW, no lidar hint
    assert mission.step(.1,None,-math.inf,.1,0.,.01,0.)[2]=='DIRECTION_SET'
    assert mission.selected_direction=='cw'
