# Main decisions during development

What was decided, why, and where the evidence is. This is a selection translated from the Spanish notes. The decisions about the final car are in the [main README](../../README.md#8-systems-thinking-and-engineering-decisions). All dates are in 2026. Lab and simulator counts are valid rounds with estimated points.

## Method

| When | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 6 Oct | **Honest simulation only.** The strategy receives LiDAR, gyroscope and camera with noise. The true pose is recorded apart, for the judge. | Earlier Open profiles used the simulator's distance, a perfect heading and noise-free sensors. The real car has none of that and has no encoder. | [`simulacion-honesta.md`](docs/simulacion-honesta.md) |
| 9 Oct | **The measured car is the default model** (steering, motor, LiDAR, IMU, camera). | Results on an idealised car did not say what the real one would do. | [`simulacion-coche-real.md`](docs/simulacion-coche-real.md) |
| Oct | **Record every attempt** and rank by points first, then by the whole time from Start. | A fast round that skips sections, or only the successful tries, would give a false picture. | [`round-scoring.md`](docs/open-challenge-runs/round-scoring.md), [`ROUNDS.md`](ROUNDS.md) |
| 26 Oct | **Heavy batches run without a window** on a second computer; final candidates are checked with a window. | Hundreds of rounds are needed to tell an improvement from noise. | [`maquina-remota.md`](docs/maquina-remota.md) |
| Nov | **A new idea starts switched off** and is adopted only if it improves on two sets of noise seeds. | With one seed and ten fields, some changes looked like improvements and were noise. | [`obstacle-v3.md`](docs/obstacle-v3.md) |

## Open Challenge

| When | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 21 to 26 Oct | **Rewrite the Open as version 5** with as few states and parameters as possible, then delete versions 1 to 4. | Version 4 had grown to 8 states and 49 parameters. | [`open-reimpl-v5.md`](docs/open-reimpl-v5.md) |
| 4 Nov | **Integrate the gyroscope with the measured time step.** | The node assumed 50 Hz but ran at about 38 Hz on the Pi, so it believed it had turned less than it had and left corners towards the inner wall. | [`open-estado.md`](docs/open-estado.md) |
| 12 Nov | **Remove eight parameters or constants** and estimate the distance to the front wall between LiDAR scans. | With the measured LiDAR gaps, rounds without a crash went from 46 % to 79 % in the lab; without gaps they stayed at 100 %. | [`open-simplificacion-20261112.md`](docs/open-simplificacion-20261112.md) |
| 12 Nov | **Brake before corners.** | Driving corners at cruise speed left only 39 % good rounds. | same note |
| 12 Nov | **Measure every change from nine start poses.** | Two regressions passed unnoticed when only one start pose was tested. | same note |
| 12 Nov | **Drop the LiDAR odometry from the Open** and use how much closer the front wall is. | 2590 of 2592 against 2591 of 2592 with odometry. Estimating distance from the commanded speed was tried and rejected (730 of 864). | same note |
| 12 Nov | **Stop dead at the finish**, with no deceleration ramp. | With the ramp, the car kept rolling with the wheels turned; the lab counted about 20 % of those finishes as valid for the judge. | same note |

## Obstacle Challenge

| When | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 1 Nov | **Do not raise the cruise speed** even when the map is known. | It saved almost no time and broke rounds: most of the time is spent under the "something close ahead" speed limit. | [`obstacle-v3.md`](docs/obstacle-v3.md) |
| 1 Nov | **Rejected:** two fixed lanes, a contact guard that reverses inside a corner, and faster parking. | Each gave fewer valid rounds. | same note |
| 1 Nov | **Score corner lines by simulating the car** and drive slowly where there is little room. | With parking, 156 against 145 of 200 in the first test. | same note |
| 1 Nov | **Choose the faster of the two best variants.** | The other scored 0.5 points more in the lab but often passed 160 s and ran out of time in Gazebo. | same note |
| 1 Nov | **Precompute the corner table** (1083 cases at that point). | Planning a corner took 21 ms (median) and up to 73 ms on a desktop processor, several times more expected on the Pi. | same note |
| 1 Nov | **Search S corners with A\*** when the line is too tight. | With parking, from 153 to 162 and from 151 to 154 of 200. | same note |
| 8 Nov | **Run the motor on port M2 without setting a motor type**, so that the board controls the speed. | A normal zero command then stops the motor, with no board resets. | [`obstacle-runs/20261108`](docs/robot-real-pi/obstacle-runs/20261108/README.md) |
| 8 Nov | **A fixed parking manoeuvre** in which every step ends on a sensor reading. | With the real car model, complete rounds parked 145 of 200 times; with the planner, 10 were parked. | [`obstacle-aparcamiento-fijo.md`](docs/obstacle-aparcamiento-fijo.md) |
| 8 Nov | **Leave `start_ramp` and `park_replan` off** and remove `approach_max`. | None of them improved both car models. | [`obstacle-v3.md`](docs/obstacle-v3.md) |
| 11 Nov | **Steering watch:** full lock asked and the gyroscope shows little turn, so stop, centre the wheels and continue. | Two crashes in corner 6 where the car did not follow the command. | [`obstacle-estado.md`](docs/obstacle-estado.md), [log](docs/robot-real-pi/obstacle-runs/20261111/README.md) |
| 12 Nov | **Read the camera as JPEG.** | Under load on the Pi, almost no raw images reached the other process; compressed images arrived complete. | [log](docs/robot-real-pi/obstacle-runs/20261111/README.md) |
