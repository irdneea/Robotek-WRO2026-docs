# Development workspace

A copy of the workspace where the strategies were developed and measured, with its tools, simulation models and round records. It is here so that the numbers of the main README can be checked.

**It is not the code of the car.** The code that runs on the car is [`../../src`](../../src). The Obstacle here (`src/robotek_obstacle/robotek_obstacle/v3/`) has the same origin but an earlier structure, and several files differ. The folder has a `COLCON_IGNORE` file, so `colcon build` at the root never sees it.

Notes, comments and records in this folder are in Spanish, the working language during development. They are kept as they were written.

## What is inside

| Folder | Content |
| --- | --- |
| `tools/` | Batch labs (`obstacle_lab_suite.py`, `open_suite_quiet.sh`), comparisons (`compare_*_suites.py`), round summary (`round_digest.py`), corner table generator (`build_corner_table.py`), steering identification (`open_lab/`), Pi and network helpers |
| `src/robotek_evaluation/` | The judge, the labs, the car models `real_car_v1` to `v4`, Gazebo runners and reports |
| `src/robotek_obstacle/`, `src/robotek_open/` | The strategies as developed here |
| `src/robotek_hardware/` | Includes the bench tests of the actuators, the board and the power |
| `docs/obstacle-challenge-runs/`, `docs/open-challenge-runs/` | Round records of the simulator |
| `docs/robot-real-pi/` | Tests and rounds on the real car, camera frames, RViz layouts, CAD of two brackets |
| `docs/*.md` | State pages, design notes and investigation notes, failed attempts included. Start with `docs/obstacle-estado.md` and `docs/open-estado.md` |
| `verification/` | Output of the runs below |

## Reproduce the lab figures

From this folder, in a terminal with ROS 2 sourced (the strategy modules import ROS message types), Python with NumPy and PyYAML:

```bash
python3 tools/obstacle_lab_suite.py --layouts 0-49 --seeds 0-1 --car real_v4 --brief
python3 tools/obstacle_lab_suite.py --layouts 0-49 --seeds 0-1 --car real_v4 --parking --brief
```

Each batch has 200 rounds. We repeated them on a Windows PC with 16 threads, replacing the ROS message packages with empty stand-ins because ROS was not installed (about 7 and 9 minutes):

| Batch | Recorded during development | Repeated |
| --- | --- | --- |
| Without parking | 195/200 valid, 123.5 s mean | **195/200, 123.5 s** |
| With parking | 127/200 valid, 159.5 s mean | **128/200, 159.3 s** |

The second differs by one round; we have not found out why. These are lab rounds with estimated points, not rounds on the car.

## What is missing or was removed

* **Raw telemetry** of most simulator rounds. Git has ignored it since 9 Oct 2026, so only the summaries are here.
* **Third-party material:** the WRO rules and playfield artwork, Hiwonder manuals and shop screenshots, and vendor packages. Without the playfield texture, `robotek_game_field.sdf` shows no mat drawing; use the open field.
* **Private data:** e-mail addresses, network addresses and user names in paths were replaced by placeholders. Two photos with people or the room were left out. Set your own addresses before using the remote or car scripts.
* Links inside the notes may point to files that were not copied.
* Apart from the two lab batches above, we have not re-run these tools in this copy (`round_digest.py` was tried on one record).
