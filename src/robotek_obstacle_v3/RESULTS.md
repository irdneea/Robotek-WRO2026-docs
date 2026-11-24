# Simulation results of the Obstacle v3 (3 Nov 2026)

These are the Gazebo and lab results of 3 Nov 2026, before the real-car profile of 8 Nov. They are **estimated points of simulation**, not an official score. Every round has the parking lot, noise seeds 0 to 2 and fields 0 to 4 in both directions (30 rounds per row).

## Same decisions as the trainer's version

The `Strategy` of this package and the original mission, connected as its own node, were run on the same fields and seeds in our lab. The 30 trajectories are **identical row by row** (the pose every 0.1 s for the whole round), with the same points and time. The comparison harness needs code of another repository and is not included here.

## Lab results

| Lab | Valid | Mean points | Mean time of the valid ones |
| --- | --- | --- | --- |
| `obstacle_lab`, with this repository's vehicle measurements | 23/30 | 47.4 | 143.6 s |
| Same strategy with the other repository's measurements | 24/30 | 48.0 | not recorded |
| The other repository's lab | 21/30 | 46.2 | 143.2 s |

```bash
python3 -m robotek_evaluation.obstacle_lab --strategy robotek_obstacle_v3.strategy:Strategy --parking --layouts 0-4 --seeds 0-2
```

The same fields fail in the same way in both labs:

* **field 2, CCW**: hits green sign 3 at 28 s (3 points), on every seed;
* **field 3, CW**: parks but goes over 180 s (37 points), on every seed.

The differences are in the parking (touching a limit of the lot in some seeds) and they come from the simulators: one of them models the 3D occlusion of the camera and uses another noise sequence.

## Gazebo with the GUI

`obstacle_round.launch.py strategy:=robotek_obstacle_v3 seed:=1 direction:=ccw parking:=true`, at 1× speed, with the real car's camera, LiDAR and actuators.

| Round | Points | Time from Start | Laps | Parking | Valid |
| --- | --- | --- | --- | --- | --- |
| `20261103T225820-v3-port-gui-reg1-ccw-park` | 55/55 | 129.26 s | 28.9 / 26.3 / 26.6 s | complete, parallel | yes (3.7 cm margin) |

The lab gives 130.0 s on the same field. There were 9 short `WAIT_SENSOR` pauses of 20 to 150 ms: a sensor arrived more than 0.35 s late, as the original node does. An earlier attempt made 40 points and did not park because of a bug in `drive.py` (the `park=0` default overrode `parking:=true`); it is fixed and covered by `test_drive.py`.
