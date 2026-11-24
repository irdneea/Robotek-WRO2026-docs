# 05 · Reproducibility: build, run and test

*Rubric criterion 5.* How another team rebuilds the car, installs the software, runs the challenges and repeats our tests. The mechanical build is in [01](01-mobility-and-mechanical-design.md) and the assembly steps are in the README; electronics in [02](02-power-and-sensor-architecture.md).

## 1. Software installation (Raspberry Pi 5)

Requirements: Raspberry Pi 5, Ubuntu 24.04 (arm64), ROS 2 Jazzy, the RRC Lite board, the LD19 LiDAR and the Pi camera connected as in [02](02-power-and-sensor-architecture.md).

```bash
git clone https://github.com/ilovmangos/Robotek-WRO2026.git
cd Robotek-WRO2026
bash tools/setup-pi.sh          # ROS dependencies, udev rules (tools/99-robotek.rules), user groups, colcon build
source install/setup.bash
```

If the script adds the user to new groups (`dialout`, `video`, `gpio`), log out and in again. After building, any change to a package needs `colcon build --packages-select <package>` again, because the installation is a copy.

## 2. Running the challenges

Wait until both board LEDs are **green**, then press the board button **once**: it is the Start. A second press stops the car.

```bash
# Obstacle Challenge: start in the lot, three laps, partial park and the validated finishing pulses
bash tools/obstacle-round.sh

# Open Challenge (three laps, wall following)
bash tools/car-run.sh open
```

`obstacle-round.sh` is the exact command validated on 12 Nov 2026. It stops any leftover node first (`tools/car-clean.sh`) so that two strategies never publish speed commands at once, and it runs with the profile `src/robotek_obstacle_v3/config/car_picam_park_round.yaml` (team field lot: far limit 0.31 m, length 0.3675 m).

**Before each round:** lift the car and invert the steering lock several times to check that the wheels follow (`tools/steer_calibration.py`); check the battery with the LEDs; check that Wi-Fi is off for the official run ([rules compliance](rules-compliance.md)).

## 3. Tests without the car

```bash
# unit tests of the Obstacle package
cd src/robotek_obstacle_v3 && python3 -m pytest test -q

# honest kinematic lab: 10 fields, both directions, with the parking lot
python3 -m robotek_evaluation.obstacle_lab --strategy robotek_obstacle_v3.strategy:Strategy --parking --layouts 0-4
```

The lab uses only LiDAR, gyroscope and camera, with noise (see [03](03-software-architecture-and-obstacle-strategy.md#testing-and-tuning-process-with-metrics)). The Gazebo simulator is launched from `robotek_gazebo`. Both write the same record as the car.

## 4. Round records

Every round on the car writes a folder `~/runs/<date>-obstacle-v3/` with `params.yaml` (the parameters used), `events.jsonl` (state changes, laps, signs, recovers, faults), `telemetry.csv` (pose, commanded speed and steering, LiDAR sectors, rear distance) and the LiDAR scans. The rule for a round record is: the whole attempt of three laps, times from Start to the end with the laps as partial times, estimated points separated from validated ones.

### Obstacle rounds on the car

| Date | Round | Result | Notes |
| --- | --- | --- | --- |
| 11 Nov 23:56 | Obstacle v3, 1:1 gears | Crash in corner 6 at 58 s | Full lock with almost no turn; led to `steer_watch` |
| 11 Nov 23:59 | Obstacle v3 | Crash in corner 6 at 55 s | Same cause |
| 12 Nov 00:02 | Complete round, no lot exit, no parking | **107.1 s** from Start; laps 36.2 / 33.1 / 33.8 s; 12 corners; no recover | The coach: perfect round. No judge, points not validated |
| 12 Nov 01:22 | Lot exit, three laps and the partial park | **105.9 s** to DONE; laps 34.3 / 26.8 / 25.1 s; 19 of 19 signs passed on the right side; partial park at 29°; five front recovers on the north side | No official total |
| 12 Nov 02:39 | Parking-only test, CCW | 20.3 s, parallel in the lot (the coach) | CW: one attempt ended about 20 cm past the lot, another started too early and hit the left limit |

Simulation lab, 50 fields × 2 directions × 2 noise seeds, `real_v4` car: **195 of 200** valid rounds without parking (mean 123.5 s) and **127 of 200** with parking (mean 159.5 s).

## 5. Test plan before the final

1. Measure and record the **mass** and **height** of the car with all parts (limits in the rules: 1.5 kg and 300 mm).
2. Measure the **current** of the electronics battery with a clamp meter during a complete round and update the power budget in [02](02-power-and-sensor-architecture.md#3-power-budget).
3. Run 10 complete Obstacle rounds in each direction and record points, time and faults in the table of this page.
4. Re-tune the HSV bands with the venue's light.
5. Check the parking pulses in CW; if they do not hold, park only in CCW and document the limit.

## 6. Versioning

Releases are listed in [CHANGELOG.md](../CHANGELOG.md): `v1.0` is the repository as it stood on 4 Nov 2026 (earlier README and scripts); `v2.0` is the version for the final: the real ROS 2 workspace (Obstacle of 12 Nov 2026) with the documentation set.
