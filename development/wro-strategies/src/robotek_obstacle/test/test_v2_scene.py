"""Obstacle v2: lane geometry, settings and the side rule (no simulator)."""
import math

import pytest

from robotek_common.vehicle import OUTLINE_HALF_WIDTH
from robotek_obstacle.v2 import scene
import itertools

from robotek_obstacle.v2 import corner
from robotek_obstacle.v2.mission import HOLD, Mission
from robotek_obstacle.v2.settings import Params, make, validate


def test_lane_starts_on_the_bottom_straight():
    x, y, heading = scene.lane_pose(0.0)
    assert (x, y) == pytest.approx((-0.5, -1.0))
    assert heading == pytest.approx(0.0)


def test_lane_turns_a_quarter_circle_per_corner():
    x, y, heading = scene.lane_pose(2.0)
    assert (x, y) == pytest.approx((1.0, -0.5))
    assert heading == pytest.approx(math.pi / 2)
    x, y, heading = scene.lane_pose(4.0)
    assert (x, y) == pytest.approx((0.5, 1.0))
    assert heading == pytest.approx(math.pi)


def test_lane_closes_after_one_lap():
    a = scene.lane_pose(0.0)
    b = scene.lane_pose(scene.UNITS_PER_LAP)
    assert b[0] == pytest.approx(a[0])
    assert b[1] == pytest.approx(a[1])
    assert math.cos(b[2] - a[2]) == pytest.approx(1.0)


def test_advance_scales_straights_and_corners():
    assert scene.advance(0.0, 0.5) == pytest.approx(0.5)
    assert scene.advance(1.0, scene.CORNER_UNITS) == pytest.approx(2.0)


def test_normal_points_to_the_island_on_the_bottom_straight():
    nx, ny = scene.lane_normal(0.0)
    assert (nx, ny) == pytest.approx((0.0, 1.0))


def test_settings_reject_unknown_parameters():
    with pytest.raises(ValueError):
        validate({'plan_speed': 1.0})
    params = make({'cruise_speed': 0.3})
    assert isinstance(params, Params)
    assert params.cruise_speed == 0.3


def _mission_with_seats(phi, seats):
    mission = Mission()
    mission.phi = phi
    mission._seats = {int(s * 2) % 16: [lateral, {colour: 3} if colour else {}, 3]
                      for s, (lateral, colour) in seats.items()}
    mission.profile = mission._plan()
    return mission


def test_plan_holds_the_side_offset_around_a_sign():
    mission = _mission_with_seats(0.0, {0.5: (-0.1, 'green')})
    expected = -0.1 + mission.p.pillar_clearance + OUTLINE_HALF_WIDTH
    for progress in (0.5 - HOLD, 0.5, 0.5 + HOLD):
        assert mission._offset_at(progress) == pytest.approx(expected)


def test_plan_remembers_a_colour_a_lap_later():
    mission = _mission_with_seats(8.2, {0.5: (-0.1, 'red')})
    assert mission._offset_at(8.5) < -0.1


def test_lookout_brings_the_line_to_the_island_side_before_an_unknown_corner_sign():
    mission = _mission_with_seats(0.0, {2.0: (0.1, None)})
    assert mission._offset_at(0.5) > 0.1


ROWS = [(0.1, 'green'), (0.1, 'red'), (-0.1, 'green'), (-0.1, 'red'), None]


@pytest.mark.parametrize('sign_a,sign_b', list(itertools.product(ROWS, ROWS)))
def test_every_corner_has_a_line_with_clearance(sign_a, sign_b):
    gap, d_a, d_b, radius = corner.plan(sign_a, sign_b, 0.0, 0.0)
    # The two crossings (inner green -> outer red and back) are the tightest: 3.4 and 4.0 cm.
    assert gap >= 0.03
    assert radius >= 0.5


def test_corner_line_passes_both_signs_on_their_side():
    gap, d_a, d_b, radius = corner.plan((0.1, 'green'), (-0.1, 'red'), 0.0, 0.0)
    assert d_a > 0.1 and d_b < -0.1
    knots = corner.knots(d_a, d_b, radius)
    assert knots[0][1] == pytest.approx(d_a)
    assert knots[-1][1] == pytest.approx(d_b)


def test_cw_colours_are_swapped_in_the_mirrored_lane():
    mission = Mission()
    mission._obs_stamp = 1.0
    mission._direction_scan = 0.5
    mission._observations = [{'x': 0.2, 'y': 0.1, 'color': 'red'}]
    cluster = {'x': 0.2, 'y': 0.1}
    assert mission._colour(cluster, sign=1.0) == 'red'
    assert mission._colour(cluster, sign=-1.0) == 'green'
