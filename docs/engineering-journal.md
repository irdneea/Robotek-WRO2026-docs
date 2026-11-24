# Engineering journal

The story of the engineering work, in order, with the reason for each change. Product details are in the numbered documents; this page is the timeline that connects them.

| Date | What happened | Decision / change |
| --- | --- | --- |
| 2024 | Version 1: cardboard prototype to understand Ackermann and component placement | Move to acrylic chassis and printed housings (versions 2–5) |
| 2024–2025 | Stepper-and-rack steering, then Hiwonder kit linkage; Raspberry Pi 4 → Pi 5 and ROS 2 | The kit linkage replaced the printed rack (imprecise teeth, collisions); ROS 2 split the system into nodes |
| 1 Aug 2026 | Repository created for WRO 2026 | Documentation and models start here |
| Aug–Sep 2026 | Versions 9–11: two-level layout, new base, lighting ring, TB6612FNG driver | See [vehicle-history.md](vehicle-history.md) |
| 7–8 Oct 2026 | Real-car tests: servo, motor, wheel angle by circles, power log | Motor "worked only sometimes": two software bugs found; wheel table measured (19.7° left / 17.6° right at 25°) |
| 9 Oct 2026 | USB topology measured; udev names; motor given its own battery | See the power evidence in [02](02-power-and-sensor-architecture.md#2-why-two-batteries-measured-evidence) |
| 1 Nov 2026 | Motor and servo moved to the RRC Lite board; servo calibration | Closed-loop speed on the board |
| 4 Nov 2026 | USB hub disabled by noise during a run; motor port moved to M2 | Relaunch procedure, retry in the board node |
| 8 Nov 2026 | Real-car model in the lab (`real_v3`) | The strategy is tuned with the real motor response |
| 9 Nov 2026 | Camera 0.35–0.43 s late 48 times in one round | Camera age limit 0.8 s |
| 11 Nov 2026 | First rounds with 1:1 gears and recording; two crashes in corner 6 | Analysis of commanded steering against gyro: the servo did not follow; `steer_watch` added |
| 12 Nov 2026 | Complete rounds: **107.1 s**, then **105.9 s** with lot exit and partial park; parking-only test parallel in the lot; the camera stalled once at 14.5 s | `CAMERA_LOST`, front recover only when full lock away still hits, rear sensor stops reverses; the coach's finishing pulses saved as the validated command |
| 18 Nov 2026 | Steering faults again; the servo mounting was found wrong on the car | Re-mounted; faults reduced. A new set of vision and planning experiments was tried in a separate branch |
| 23 Nov 2026 | Decision for the final | Keep the validated 12 Nov Obstacle; keep the experiments in a branch; update the documentation to the real car |
| 24 Nov 2026 | Documentation restructured by the five criteria; real code added to the repository | See [CHANGELOG.md](../CHANGELOG.md) |

## What we learned

1. A planned line is only as good as the steering that follows it: half of our crashes were a servo or a mounting, not the strategy. Logging the *commanded* and the *measured* turn side by side was the tool that found them.
2. The limit of the real system was the slowest sensor (the camera) and the lowest motor speed, not the algorithms.
3. A validated version beats a better untested one two weeks before the final.
