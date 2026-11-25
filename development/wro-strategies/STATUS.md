# Where the development stood

An English summary of the two state pages, [`docs/open-estado.md`](docs/open-estado.md) (dated 12 Nov 2026) and [`docs/obstacle-estado.md`](docs/obstacle-estado.md) (dated 8 Nov, with entries up to 12 Nov). It describes the development notes, not a new test. For the code that runs on the car and its results, see the [main README](../../README.md).

Simulator and lab points are **estimates**. No round here has a score from a judge.

## Open Challenge

**Strategy.** Version 5 is the only Open strategy; versions 1 to 4 were deleted from this workspace and their round records were kept. In this copy: `src/robotek_open/robotek_open/v5/`.

**Lab figures after the simplification of 12 Nov** ([note](docs/open-simplificacion-20261112.md); final section of the note):

| Test | Result |
| --- | --- |
| 16 inner-wall layouts × 2 directions × 9 start poses × 9 noise seeds, `real_v4` car, gyroscope reading 94 % of the turn | 2576 of 2592 good rounds (99.4 %), 2575 valid for the rule judge |
| Same 16 layouts, 2 directions and 9 start poses, 3 seeds, exact gyroscope | 864 of 864 |
| Stress test with LiDAR gaps | 75 % good |
| Simulator car model (`real_v1`) in the lab, standard set of 12 | 60 of 60, 41.92 s mean |

These are lab rounds. The simplified version was not run in Gazebo with a window.

**LiDAR gaps.** The LD19 driver polled at 10 Hz while the sensor turns at 9.9 Hz, so it lost whole turns. After polling at 200 Hz, the Pi measured no gap in 60 s with the car standing still. The state page says this still had to be confirmed during a moving round.

**Older figures on the same page** were measured before the simplification: 12 of 12 in the lab (40.73 s mean), 12 of 12 twice in Gazebo without a window, and a 30-point round with a window in 33.2 s (CCW) and 32.9 s (CW). The best recorded simulator round with a window, 29.3 s on 8 Oct, used [another profile and car model](docs/open-challenge-runs/best-realcar-open-round.md) and cannot be compared with version 5.

**On the real car.** The notes record the tests of [4 Nov](docs/robot-real-pi/open-runs/20261104/README.md) (from "the motor does not move the car" to complete rounds) and [8 Nov](docs/robot-real-pi/open-runs/20261108/README.md) (three rounds that the operator called perfect, 28.7 to 30.4 s from Start to DONE).

**Open points when the page was written:** repeat the Gazebo standard set with the corrected car model, and check on the car where it stops with `finish_lead` 0.14, a value that came from the lab.

## Obstacle Challenge

**Strategy.** Version 3 is version 2 plus corner lines scored by simulating the drive, lines searched with A\* for S corners, a precomputed corner table, slow driving in corners with little room and a different way of passing signs whose colour is not known yet ([report](docs/obstacle-v3.md)).

**Furthest points reached on the car, night of 11 to 12 Nov** ([log of that night](docs/robot-real-pi/obstacle-runs/20261111/README.md)):

| Time | What happened |
| --- | --- |
| 00:02 | Three laps without the parking lot or parking, DONE 107.1 s after Start |
| 00:51 | Lot exit, three laps and a partial park, DONE 111.6 s, 26 of 26 sign passes on the correct side |
| 01:22 | Lot exit, three laps and a partial park, DONE 105.9 s, 19 of 19 recorded sign passes correct |
| 02:39 | Parking-only test, CCW: parallel inside the lot according to the coach |
| 02:46, 03:05 | CW parking failed: the position along the straight was 20 to 30 cm wrong |

**Lab, 50 fields × 2 directions × 2 noise seeds (200 rounds), table from the log of that night:**

| Car model | Without parking | With parking |
| --- | --- | --- |
| `real_v3` | 192 valid, 124.1 s | 125 valid, 161.3 s |
| `real_v4` | 195 valid, 123.5 s | 127 valid, 159.5 s |
| `real_v4`, gyroscope reading 94 % | 195 valid, 123.5 s | 131 valid, 159.1 s |

The state page has older parking figures for `real_v3` (8 of 200 valid with the planner, 138 with the fixed manoeuvre). The log does not say which parking setting its 125 used.

`real_v4` was fitted with the 54:30 gears. The car later ran with 1:1 gears, and that response had not been measured for the model.

**Parking alone**, `real_v3`, lot length 0.3675 m (1.5 × the measured car length of 0.245 m), 200 rounds: the fixed manoeuvre parked 197 and the planner 173 ([note](docs/obstacle-aparcamiento-fijo.md)). Complete rounds had not been repeated with that lot length; with the earlier 0.3495 m lot the fixed manoeuvre gave 145 parked and 138 valid rounds.

**Missing when the notes end:**

1. CW parking on the car. The new option `park_fixed_sense:=2` had only been tried in the model.
2. A complete round that uses the final parking pulses. The parallel result came from the parking-only test.
3. A full parallel park checked with a ruler. The verdict was the coach looking at the car.
4. The position of the lot on the competition field. The team's field and the rules differ (0.31 m and 0.48 m in the parameter `park_lot_end`).
5. The steering that sometimes did not follow the command in corner 6. The watch stops the car, but the cause was not found.
6. Three to five `front_recover` manoeuvres per round in the north corners.
7. A final value for the minimum motor speed (`motor_min_rps`), a check of the sign colours under other light, and a lab model for the 1:1 gears.
8. Time. With parking, the lab rounds take about 160 s of the 180 s limit.
