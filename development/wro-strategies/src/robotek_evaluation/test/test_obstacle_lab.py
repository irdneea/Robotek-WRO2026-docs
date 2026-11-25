"""Obstacle lab: world parsing, LiDAR rays, camera observations and a short round."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from robotek_evaluation import obstacle_experiment_setup, obstacle_lab


@pytest.fixture(scope='module', autouse=True)
def _rebuilt_round(tmp_path_factory):
    """The world of the recorded round obs-base-a-reg0-ccw is not in git, so it is generated again (layout 0).

    The round's own manifest is kept, and the signs of the generated world must be the recorded ones: that checks that
    the generator still builds the field that was recorded. The record itself is not modified.
    """
    global _ROUND
    rounds = sorted((Path(obstacle_lab.ROOT) / 'docs' / 'obstacle-challenge-runs').glob('*-obs-base-a-reg0-ccw'))
    if not rounds:
        pytest.skip('no recorded obstacle round to reuse')
    manifest = json.loads((rounds[-1] / 'manifest.json').read_text())
    folder = tmp_path_factory.mktemp('obs-reg0-ccw')
    pillars = obstacle_experiment_setup.build_world(folder, 0, Path(obstacle_lab.ROOT))

    def seats(signs):
        return sorted((round(p['x'], 3), round(p['y'], 3), p['color']) for p in signs)

    assert seats(pillars) == seats(manifest['pillars'])
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    _ROUND = folder


def _round():
    return _ROUND


def test_world_reads_walls_and_signs():
    world = obstacle_lab.World(_round())
    assert len(world.wall_boxes) == 8
    assert set(world.kinds) == {'inner_wall', 'outer_wall'}
    assert len(world.sign_boxes) == len(world.pillars) == 5


def test_raycast_hits_a_wall_and_a_sign():
    world = obstacle_lab.World(_round())
    # From the start, looking forward (+x) sees no wall within the corridor length.
    ranges = world.raycast(0.0, -1.0, np.array([0.0]))
    assert ranges[0] == pytest.approx(1.5, abs=0.02)
    # Looking left (+y) from the bottom straight sees the inner wall at 0.5 m.
    ranges = world.raycast(0.0, -1.0, np.array([math.pi / 2]))
    assert ranges[0] == pytest.approx(0.5, abs=0.01)


def test_camera_only_reports_signs_in_front_and_close():
    world = obstacle_lab.World(_round())
    rng = np.random.default_rng(0)
    pillar = world.pillars[0]
    # Beyond the colour range: nothing reported even facing the sign.
    assert obstacle_lab.camera_observations(world, pillar['x'] - 1.5, pillar['y'], 0.0, rng,
                                            max_range=0.2) == []
    # 0.6 m behind the sign, facing it: the sign is reported with its colour.
    x, y, yaw = pillar['x'] - 0.6, pillar['y'], 0.0
    observations = obstacle_lab.camera_observations(world, x, y, yaw, rng)
    assert any(o['color'] == pillar['color'] for o in observations)


def test_short_round_returns_a_judged_result():
    result = obstacle_lab.run_round(_round(), tmax=6.0)
    assert result['points'] is not None
    assert result['direction'] == 'ccw'
    assert 'failed' in result


def _signs_world(positions):
    """World with only 50 x 50 x 100 mm signs at ``positions`` (no walls), for the camera tests."""
    world = object.__new__(obstacle_lab.World)
    world.pillars = [dict(x=x, y=y, color='red', size_m=[.05, .05, .1]) for x, y in positions]
    world.wall_boxes = np.zeros((0, 4))
    world.sign_boxes = np.array([(x - .025, x + .025, y - .025, y + .025) for x, y in positions])
    world.view_boxes = world.sign_boxes
    world.view_tops = np.full(len(positions), .1)
    return world


def test_camera_occlusion_hides_signs_behind_a_near_one_but_sees_over_it():
    # Alone: seen.
    assert obstacle_lab._seen(_signs_world([(1.0, 0.0)]), 0.0, 0.0, 0)
    # Behind a sign at half its distance only its top (~4 cm of 10) shows: wider than tall, rejected.
    assert not obstacle_lab._seen(_signs_world([(0.5, 0.0), (1.0, 0.0)]), 0.0, 0.0, 1)
    # Far behind a very near sign the camera (14.2 cm high) sees it whole over the near one.
    assert obstacle_lab._seen(_signs_world([(0.3, 0.0), (1.5, 0.0)]), 0.0, 0.0, 1)
    # Beside the near sign's line of sight: seen.
    assert obstacle_lab._seen(_signs_world([(0.5, 0.0), (1.0, 0.3)]), 0.0, 0.0, 1)
