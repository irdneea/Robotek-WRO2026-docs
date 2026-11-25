"""The precomputed v3 corner table matches the planner (run tools/build_corner_table.py if not)."""
import random

from robotek_obstacle.v3 import corner
from robotek_obstacle.v3.corner_table import TABLE


def test_table_covers_the_mission_and_matches_the_planner():
    assert len(TABLE) > 500
    family = [args for args, value in TABLE.items() if value is None or len(value) != 2]
    for args in random.Random(0).sample(sorted(family, key=repr), 12):
        expected = corner._choose(args)
        assert TABLE[args] == (None if expected is None else tuple(float(v) for v in expected)), args


def test_searched_lines_beat_the_family_line():
    searched = [args for args, value in TABLE.items() if value is not None and len(value) == 2]
    for args in random.Random(0).sample(sorted(searched, key=repr), min(4, len(searched))):
        gap, (kind, knots) = TABLE[args]
        assert kind == 'k' and len(knots) > 10
        assert gap >= corner._choose(args)[0] + 0.005, args
