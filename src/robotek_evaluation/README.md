# robotek_evaluation

Everything that **only exists in simulation** and that a strategy must never use (the real car has none of it):

| Module / node | What it does |
| --- | --- |
| `rule_judge.py` | The judge: points according to the rules (sections, laps, stop) and the standard validation (no contact, margin, steering within ±25°) |
| `contact_recorder` | Records the contacts of the car with the walls (`contacts.jsonl`, one line per episode, see `contact_log.py`) |
| `sim_actuator_model` | The real car's servo and motor (delay, angular speed limit, speed table) between the strategy node and Gazebo |
| `sim_scan_model` | The rays the LD19 LiDAR loses (4.3 % at random) |
| `open_lab.py` | The Open lab: the field and the car in plain Python, a few seconds per round. A fast filter; Gazebo has the last word |
| `obstacle_lab.py` | The same for the Obstacle Challenge, with the parking lot and the sign layouts |
| `open_field_geometry.py`, `footprint.py` | Geometry of the walls and footprint of the car |

The referee of a round (`round_recorder`) and `score` live in `robotek_course`.

```bash
python3 -m robotek_evaluation.open_lab --strategy <module>:<Strategy class>   # the twelve rounds of the standard set
python3 -m robotek_evaluation.obstacle_lab --strategy robotek_obstacle_v3.strategy:Strategy --parking --layouts 0-4
```

It depends on `robotek_common`. No strategy depends on this package.
