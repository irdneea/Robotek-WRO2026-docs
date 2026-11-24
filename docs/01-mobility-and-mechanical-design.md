# 01 · Mobility and mechanical design

*Rubric criterion 1.* This page explains the chassis, the steering, the drive train, the reasoning behind each choice and the tests that changed the design. Photos of the car from every side, top and bottom are in [`v-photos`](../v-photos), the printed parts are in [`models`](../models) and the eleven versions of the car are in [vehicle-history.md](vehicle-history.md).

## 1. Layout and dimensions

| Item | Value | Source |
| --- | --- | --- |
| Layout | Four wheels, **rear-wheel drive** (one driven axle), **Ackermann steering** on the front axle | rules 11.3 |
| Wheelbase | 118.83 mm (front kingpins to rear axle) | STEP model + caliper, `robotek_obstacle_v3/car.py` |
| Rear track / outer width | 123.5 mm / 138.0 mm (caliper); 147.6 mm over the front wheels | caliper, 21 Oct 2026 |
| Chassis plate | 189 mm long, 90 mm wide | STEP model |
| Outline used by the planners | 147.0 mm ahead of the reference point (LiDAR tab) and 85.9 mm behind it: about 233 mm long | `car.py` |
| Wheels | 3D-printed rims with a 61.0 mm silicone tyre (suitcase wheel protector), 14.5 mm wide, same on all four wheels since version 10 | [vehicle-history.md](vehicle-history.md) |
| Limits of the rules | 300 × 200 mm, 300 mm high, 1.5 kg | rules 11.1 and 11.2, see [rules compliance](rules-compliance.md) |

The reference point of the software (`base_link`) is midway between the axles, on the floor. Every sensor offset (LiDAR 127.3 mm ahead, camera 55.8 mm ahead) is measured from it and must match the URDF in `src/robotek_description`.

## 2. Steering: why a Hiwonder Ackermann linkage

**Choice.** A linkage Ackermann from the Hiwonder kit driven by one 15 kg·cm digital servo.

**Why.** Our first versions used a stepper motor with a 3D-printed gear and rack. Small printed teeth were imprecise and the rack collided with the servo in version 8–9, so we replaced it by the kit linkage, adapted to our chassis. Ackermann geometry makes all wheels roll around a common centre, which cuts tyre slip in the tight corners of the field (inner lane radius of about 0.4 m).

**What testing changed.**

1. *Servo position.* With the servo horizontal under the linkage the car turned worse to the left than to the right (limited servo angle). Moving the servo to a vertical position fixed the asymmetry (photos in [vehicle-history.md](vehicle-history.md)).
2. *Servo placement, again, on 18 Nov 2026.* After the Obstacle rounds of that day showed full-lock commands with almost no turn (gyro 0.01–0.2 rad/s where 0.5–1.2 rad/s was expected), the servo mounting was found to be wrong on the car. It was re-mounted and the number of steering faults per round dropped (9 in the worst round before, 0–3 after), although not to zero, so the check stays on. The software now watches for this failure (`steer_watch.py`): full lock asked while driving forward and the gyroscope shows less than 30 % of the expected turn.
3. *Real wheel angle.* We measured the wheel angle with circles on the floor (`tools/steer_calibration.py`, 8 Oct and 1 Nov 2026): at the servo limit of 25° the wheels reach about **19.7° to the left and 17.6° to the right**. `base_adapter` converts the commanded wheel angle to servo microseconds through a measured table (centre 1403 µs, 20 µs per servo degree, `src/robotek_hardware/config/robot.yaml`) and the strategies are limited to **17.5°** of wheel angle, so a command is never beyond what the car can do. The servo itself is also limited to 25° (the limit the team set for the software).

**Trade-off.** More steering angle would give tighter corners but the linkage binds beyond 25° of servo, so the minimum turning radius is fixed by geometry (about 0.38 m at 17.5°). Our corner planner (`corner.py`) is written around that radius instead of assuming ideal steering.

## 3. Drive train: motor, gears, speed

**Motor.** One Hiwonder JGA27-310R encoder motor (20:1 gearbox, 450 rpm) on port M2 of the RRC Lite board. The board runs the speed loop with the encoder, so the software commands m/s (converted to board rps) and the speed no longer depends on battery voltage.

**Torque and speed reasoning.**

* The board's speed loop cuts the PWM below 25 %, which is about 0.2 m/s with no load for this fast motor: it cannot hold 0.15–0.30 m/s by itself. On the floor it either does not start or runs at 0.35–0.4 m/s. We therefore set a minimum command (`motor_min_rps: 2`, about 0.25 m/s) and plan the Obstacle at 0.28–0.30 m/s, the lowest speed at which the motor starts the car reliably with full steering lock.
* Above about 2 board rps the motor cannot turn faster, the board only pushes more current (a frontal crash at full push stalled and overheated it). `motor_max_rps` is limited accordingly (about 0.49 m/s).
* Measured by LiDAR runs: 1 board rps = 0.209 m/s with the first gearing, about 0.45 m/s mean and 0.65–0.69 m/s peak forward at 1.9 rps, 0.40–0.44 m/s backwards.

**Gear ratio: 54:30 against 1:1.** The first Obstacle rounds used a 54:30 reduction (`motor_rps_per_mps` 4.4). After rounds with several ratios on 11–12 Nov the coach chose **1:1** (`motor_rps_per_mps` 7.0–8.0): the car starts at lower speeds with full lock and the speed command is better aligned with the speed on the floor. Result on the same field: complete rounds of 107.1 s from Start (laps 36.2 / 33.1 / 33.8 s) with no recovery manoeuvre, and 105.9 s with the partial park. See the table in [05 Reproducibility and tests](05-reproducibility-build-and-test.md#obstacle-rounds-on-the-car).

**Motor driver history.** L298N → TB6612FNG → RRC Lite closed loop (summary in [vehicle-history.md](vehicle-history.md#motor-driver-history-what-the-table-above-does-not-say)).

## 4. Mechanical stability

* Version 9 stacked the electronics in two levels (batteries and the board below, the Raspberry Pi above) and printed a new base: lower centre of gravity and no more collision between rack and servo.
* A gap between the metal chassis part and the axle supports made the drive train wobble; we designed 3D-printed cylindrical spacers that fill it.
* A groove in the wheels plus small printed cylinders improved traction. The silicone tyres give the grip that the printed plastic did not.
* The LiDAR was moved lower (it looked over the walls at its first height) and mounted on a printed tab in front of the car (`models/lidar_housing`).

## 5. Printed parts

| Part | Folder | Purpose |
| --- | --- | --- |
| Vehicle base | [`models/vehicle_base`](../models/vehicle_base) | Chassis plate with the mounting holes of every housing |
| Raspberry Pi housing | [`models/raspberry_housing`](../models/raspberry_housing) | Holds the Pi above the servo |
| Camera housing | [`models/camara_housing`](../models/camara_housing) | Fixed inclination of the camera (see [02](02-power-and-sensor-architecture.md)) |
| LiDAR housing | [`models/lidar_housing`](../models/lidar_housing) | Puts the LD19 at the front with a free field of view |
| Wheels | [`models/vehicle_wheels`](../models/vehicle_wheels) | Rims that take the silicone tyre |

Each folder has an STL and a preview image. The kit parts (Ackermann linkage, hubs, motor, servo) are listed in the bill of materials of [02](02-power-and-sensor-architecture.md#bill-of-materials). A reproducible assembly sequence is in the README of this repository.

## 6. What we would change next

A rear VL53L0X distance sensor stops reversing moves before the car touches the parking limits (see 02). The wheel encoder is still not read by the software; using it would remove the dead reckoning drift we see after the lot exit (the estimated pose is up to 0.2 m away from the LiDAR localisation).

## 7. Torque and speed, worked out

The tyres are 61 mm in diameter, so one wheel turn moves the car 0.1916 m. The speeds we use correspond to these wheel speeds:

| Speed | Where we use it | Wheel speed |
| --- | --- | --- |
| 0.25 m/s | Slowest the motor holds (the motor floor) | 78 rpm |
| 0.28–0.30 m/s | Obstacle lane following | 88–94 rpm |
| 0.64 m/s | Open corners | 200 rpm |
| 0.85 m/s | Open straights | 266 rpm |

**How much torque does the car need?** Take the worst case allowed by the rules, 1.5 kg, a rolling resistance coefficient of 0.03 for silicone on the mat (an assumption, to be checked with a pull test) and a hard acceleration of 1 m/s². The force at the tyres is 0.03 × 1.5 × 9.81 + 1.5 × 1 = 1.94 N, which at a wheel radius of 30.5 mm is **0.059 N·m (0.6 kg·cm)** at the axle. That is small, and the motor has plenty of margin; the limit of our car was never torque, it was the **minimum speed at which the motor and its driver start moving** (see section 3), and the electrical limits of the board when the motor is blocked. This is why the gearing was chosen by what happened on the track (starting at full lock, speed at 0.28 m/s) and not by a torque calculation.

**Why the steering lock matters for speed.** At 17.6° of wheel angle and a wheelbase of 118.83 mm the turning radius of the rear axle is 0.118 83 / tan 17.6° = **0.375 m**. At 0.28 m/s the car then turns at 0.75 rad/s (43°/s). The corner planner and the steering watch use exactly this relation: if the gyroscope reads much less than speed × tan(wheel angle) / wheelbase, the wheels did not turn.

## 8. Building the mechanics, step by step

These are the steps in the order we assemble the car; the photos of the finished car from every side are in [`v-photos`](../v-photos).

1. **Base.** Print `vehicle_base` (or cut it) and fit the rear axle supports. If there is a gap between the chassis part and the supports, fit the printed spacer cylinders before tightening: a loose axle makes the drive train wobble.
2. **Drive axle.** Fix the motor mount to the base and the motor to the mount. Put the axle through its two bearings, secure it with the two locking rings and join the motor shaft to the axle with the spacers, keeping them clear of the motor screws. The rear wheels go on the hubs with the silicone tyres.
3. **Steering.** Screw the fixed Ackermann part to the base. Fit the two movable pieces on its sides and check they turn freely. Join the wheel pieces with the long linkage (bearings at both ends) and fit the shorter second linkage on the side opposite to the servo output shaft. Mount the servo **vertically** (a horizontal servo limited the left angle) so that its horn moves the short linkage. Fit the front wheel hubs on bearings.
4. **Centre the steering.** With the electronics running, send 1403 µs to the servo and tighten the horn so that the wheels point straight. Then check the left and right limits with the calibration tool (`tools/steer_calibration.py`): about 19.7° left and 17.6° right at 25° of servo.
5. **Housings.** LiDAR housing at the front with a free field of view, camera housing right behind it (inclined down about 8°), the batteries and the Raspberry Pi housing behind, over the servo.
6. **Electronics** as in the README and [02](02-power-and-sensor-architecture.md), then the checks of [05](05-reproducibility-build-and-test.md#2-running-the-challenges) before the first round.
7. **Weigh and measure** the finished car against the limits in [rules-compliance](rules-compliance.md).
