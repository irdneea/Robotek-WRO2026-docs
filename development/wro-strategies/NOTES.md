# Index of the notes

The notes are in Spanish and are kept as written. This index says in English what each one is about, so you can choose what to open. Many were written before later changes: when two disagree, the later one and the [main README](../../README.md) count.

## Current state

| Note | What it is about |
| --- | --- |
| [`open-estado.md`](docs/open-estado.md) | State of the Open, car models, how to measure (summary in [`STATUS.md`](STATUS.md)) |
| [`obstacle-estado.md`](docs/obstacle-estado.md) | State of the Obstacle, open problems, lab results (summary in [`STATUS.md`](STATUS.md)) |
| [`next-steps.md`](docs/next-steps.md) | Older project-wide log of next steps; mostly early October |
| [`README.md`](docs/README.md) | Spanish index of the notes as of 9 Oct; some of its links point to files that were not copied |

## Open Challenge

| Note | What it is about |
| --- | --- |
| [`open-reimpl-v5.md`](docs/open-reimpl-v5.md) | Rewriting the Open from scratch: study of version 4, design of version 5 and later results (its first header still calls it a plan) |
| [`open-simplificacion-20261112.md`](docs/open-simplificacion-20261112.md) | Simplifying version 5: what was removed, kept and measured |
| [`open-lab.md`](docs/open-lab.md) | The Open lab, a fast simulator without Gazebo, and how faithful it is |
| [`mapping-and-racing-investigation.md`](docs/mapping-and-racing-investigation.md) | Whether mapping the track in lap 1 could work on a Raspberry Pi 5 |

## Obstacle Challenge

| Note | What it is about |
| --- | --- |
| [`obstacle-challenge-rules-and-strategy.md`](docs/obstacle-challenge-rules-and-strategy.md) | The rules, a first implementation plan and what the top three teams of 2025 do |
| [`obstacle-v3.md`](docs/obstacle-v3.md) | Version 3: each idea tested alone, kept or rejected |
| [`obstacle-aparcamiento-fijo.md`](docs/obstacle-aparcamiento-fijo.md) | The fixed parking manoeuvre, in the lab and on the car |
| [`obstacle-deteccion-pilares.md`](docs/obstacle-deteccion-pilares.md) | Sign detection: an earlier camera-only code of the team compared with this one |
| [`obstacle-reimpl-plan.md`](docs/obstacle-reimpl-plan.md) | Plan for rewriting the Obstacle as version 2 |
| [`obstacle-reimpl-v2.md`](docs/obstacle-reimpl-v2.md) | Baseline, design and results of version 2 |
| [`obstacle-v2-next-steps.md`](docs/obstacle-v2-next-steps.md) | Version 2: remaining work, iterations and reverted experiments |
| [`obstacle-refactor.md`](docs/obstacle-refactor.md) | An earlier clean-up of the first Obstacle node, with the same behaviour |
| [`obstacle-guide-spec.md`](docs/obstacle-guide-spec.md) | Specification of a step-by-step learning guide for the Obstacle |

## Simulation and judging

| Note | What it is about |
| --- | --- |
| [`simulacion-honesta.md`](docs/simulacion-honesta.md) | What the strategy may and may not see in simulation |
| [`simulacion-coche-real.md`](docs/simulacion-coche-real.md) | Model of the measured car and its limits |
| [`juez-y-validacion.md`](docs/juez-y-validacion.md) | The rule judge and our acceptance check |
| [`roadmap-robot-nuevo.md`](docs/roadmap-robot-nuevo.md) | What had to be validated again after the car was measured anew (21 Oct) |
| [`simulacion-macos.md`](docs/simulacion-macos.md) | Simulating on a Mac: measurements and limits |
| [`guia-inicio-macos-robostack.md`](docs/guia-inicio-macos-robostack.md) | Setting up a Mac from zero |
| [`maquina-remota.md`](docs/maquina-remota.md) | The second computer for heavy batches |
| [`paquetes.md`](docs/paquetes.md) | The ROS 2 packages of this workspace and which may depend on which |

## The real car

| Note | What it is about |
| --- | --- |
| [`robot-real.md`](docs/robot-real.md) | Launching on the car and calibration (older configuration) |
| [`robot-real-pi.md`](docs/robot-real-pi.md) | First sessions on the Raspberry Pi: sensors in RViz, sign detector, servo |
| [`ros-robot-controller-oficial.md`](docs/ros-robot-controller-oficial.md) | What the official Hiwonder board node publishes and accepts |
| [`rrc-lite-motor-2024-vs-ahora.md`](docs/rrc-lite-motor-2024-vs-ahora.md) | Motor control on the board: the 2024 code against the later driver |
| [`rrc-lite-pruebas.md`](docs/rrc-lite-pruebas.md) | Tests of every function of the board, with results |
| [`plan-docs-open-obstacle-20261108.md`](docs/plan-docs-open-obstacle-20261108.md) | Plan to update two other documentation sites; internal housekeeping |

## Logs of tests on the car

| Log | What it records |
| --- | --- |
| [`open-runs/20261104`](docs/robot-real-pi/open-runs/20261104/README.md) | Open, 4 Nov: first tests, motor and brake problems, the slow-loop gyroscope error, first complete rounds |
| [`open-runs/20261108`](docs/robot-real-pi/open-runs/20261108/README.md) | Open, 8 Nov: speed-controlled motor, steering failures, three good rounds |
| [`obstacle-runs/20261104`](docs/robot-real-pi/obstacle-runs/20261104/README.md) | Obstacle, 4 Nov: first rounds; neither passed the first corner |
| [`obstacle-runs/20261108`](docs/robot-real-pi/obstacle-runs/20261108/README.md) | Obstacle, 8 Nov: motor measurements, first complete round, parking attempts |
| [`obstacle-runs/20261111`](docs/robot-real-pi/obstacle-runs/20261111/README.md) | Obstacle, night of 11 to 12 Nov: lot exit, three laps, partial and parallel parking, what is missing |

## Reports of simulator rounds

| Report | What it records |
| --- | --- |
| [`round-scoring.md`](docs/open-challenge-runs/round-scoring.md) | How points and times are recorded for each round |
| [`best-realcar-open-round.md`](docs/open-challenge-runs/best-realcar-open-round.md) | Best round with a window on the 8 Oct car model, and why it was chosen |
| [`realcar-open-history.md`](docs/open-challenge-runs/realcar-open-history.md) | Each improvement of that best round |
| [`realcar-open-validation.md`](docs/open-challenge-runs/realcar-open-validation.md) | Retuning the Open for the measured car |
| [`realcar-robust-validation.md`](docs/open-challenge-runs/realcar-robust-validation.md) | Robustness over six field shapes in both directions |
| [`realcar-robust-best-rounds.md`](docs/open-challenge-runs/realcar-robust-best-rounds.md) | Best round for each field and start |
| [`realcar-starts-history.md`](docs/open-challenge-runs/realcar-starts-history.md) | Trials from shifted start poses |
| [`best-realcar-open-round-judge-v1.md`](docs/open-challenge-runs/best-realcar-open-round-judge-v1.md), [`history`](docs/open-challenge-runs/realcar-open-history-judge-v1.md), [`validation`](docs/open-challenge-runs/realcar-open-validation-judge-v1.md) | The same three reports before the judge's sampling was corrected |
| [`actuator-model-findings.md`](docs/open-challenge-runs/actuator-model-findings.md) | The "slow steering servo" of the simulator was caused by a Gazebo plugin |
| [`honest-fsv4-validation.md`](docs/open-challenge-runs/honest-fsv4-validation.md) | Honest-mode validation of an early Open profile |
| [`parking-findings.md`](docs/obstacle-challenge-runs/parking-findings.md) | Early parking in a simulated world with an idealised fast servo |
