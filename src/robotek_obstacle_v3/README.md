# robotek_obstacle_v3

The Obstacle Challenge strategy of the car: three laps with red and green signs, starting inside the parking lot and finishing parked in it. It only uses honest sensors, the LiDAR, the gyroscope and the camera, plus the rear distance sensor. There is no encoder and no ground-truth pose.

The long explanations are in the main README. Start with these chapters:

| Topic | Where |
| --- | --- |
| Code structure and state machine | [chapter 5](../../README.md#5-software-architecture) |
| Finding signs, remembering them, choosing sides, recovering from contacts | [chapter 6](../../README.md#6-obstacle-challenge-finding-and-avoiding-the-signs) |
| Leaving the lot and parking in parallel | [chapter 7](../../README.md#7-obstacle-challenge-leaving-the-lot-and-parking-in-parallel) |
| Parameters and their defaults | [PARAMETERS.md](PARAMETERS.md) |
| Simulation results | [RESULTS.md](RESULTS.md) |

## Files

| File | What it does |
| --- | --- |
| `drive.py` | The ROS node: scan, IMU, camera, rear distance and Start in, `/cmd_vel_raw` out; records every round |
| `strategy.py` | The `Strategy` class: pauses the mission when a sensor is stale and ends the round at 180 s |
| `mission.py` | The state machine and every decision: SETUP, LOT_EXIT, RUN, PARK, STOP |
| `scene.py`, `field.py` | Lane geometry in track units and the mapping from LiDAR points to the lane |
| `localizer.py` | Pose from the walls plus the gyro heading |
| `perception.py` | LiDAR clusters the size of a sign |
| `corner.py`, `corner_table.py` | The line through each corner (the table is precomputed) |
| `lot_exit.py` | Direction from the lot and the pulses that take the car out |
| `park.py`, `park_fixed.py`, `parking_search.py` | Parking: the planned park and the fixed one that runs on the car |
| `steer_watch.py` | Detects a servo that does not follow the steering command |
| `settings.py` | Every tunable parameter, with its default |
| `recording.py` | Telemetry, events and scans of every round |
| `car.py` | Measurements of the car this strategy was tuned with |

## Running and testing

```bash
bash tools/obstacle-round.sh                 # on the car, from the repository root
cd src/robotek_obstacle_v3 && python3 -m pytest test -q
python3 -m robotek_evaluation.obstacle_lab --strategy robotek_obstacle_v3.strategy:Strategy --parking --layouts 0-4 --seeds 0-2
```
