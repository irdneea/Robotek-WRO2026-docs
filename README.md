# Renkay · WRO 2026 Future Engineers

<p align="center">
  <img src="https://github.com/user-attachments/assets/0a4118c9-bc9c-422e-af6b-4e9b3267209f" alt="Banner Renkay" width="100%">
</p>

[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/robotekperu/)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@Robotekperu)
[![Facebook](https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://www.facebook.com/p/Robotek-Per%C3%BA-61566493439700/)

**Welcome!** We are **Renkay**, a team of three students from Peru (Robotek Perú) competing in the **World Robot Olympiad 2026, Future Engineers**. This repository contains the documentation, the source code and the engineering journey of our autonomous vehicle, **Sami**: a 4-wheel, rear-drive car with Ackermann steering, driven by a Raspberry Pi 5 running ROS 2 and a Hiwonder RRC Lite controller, that perceives the field with a LiDAR, a wide-angle camera, a gyroscope and a rear distance sensor.

> [!NOTE]
> 🤔 Why is our team named *Renkay*?<br><br>
> The name *Renkay* is inspired by three words that define our team: resilience, minka, and wiñay. "**Resilience**" represents our determination to never give up; "**minka**", an ancestral tradition of working together for a common purpose, reflects our belief that the best ideas are built through collaboration; and wiñay, which means "to grow", symbolizes our commitment to continuous learning and improvement. Together, these words represent who we are as a team, and guide every step of our robotics journey.

## Contents

1. [Documentation map (read this first)](#1-documentation-map)
2. [Repository structure](#2-repository-structure)
3. [The team](#3-meet-the-team)
4. [The vehicle at a glance](#4-the-vehicle-at-a-glance)
5. [The two challenges and our strategy](#5-the-two-challenges-and-our-strategy)
6. [How to build and run it](#6-how-to-build-and-run-it)
7. [Assembly instructions](#7-assembly-instructions)
8. [Results and validation](#8-results-and-validation)
9. [Performance videos](#9-performance-videos)
10. [Rules compliance, credits, licence](#10-rules-compliance-credits-and-licence)

## 1. Documentation map

The documentation follows the five evaluation criteria of the WRO 2026 Future Engineers rubric. Each page says *what we built*, *why* (with the data that supports it) and *what we tested*.

| Criterion | Page | What you will find |
| --- | --- | --- |
| Mobility and mechanical design | [docs/01-mobility-and-mechanical-design.md](docs/01-mobility-and-mechanical-design.md) | Dimensions, Ackermann steering and why a linkage, servo mounting and the real wheel angle, drive motor, gear ratio 54:30 against 1:1, torque and speed reasoning, printed parts |
| Power and sensor architecture | [docs/02-power-and-sensor-architecture.md](docs/02-power-and-sensor-architecture.md) | Block diagram, two batteries and the measured evidence, power budget, sensor choice and placement, calibration methods, failure points, bill of materials |
| Software architecture and obstacle strategy | [docs/03-software-architecture-and-obstacle-strategy.md](docs/03-software-architecture-and-obstacle-strategy.md) | Packages and modules, state machine, perception, lane following and sign obedience, edge cases, tests and metrics |
| Systems thinking and engineering decisions | [docs/04-systems-thinking-and-engineering-decisions.md](docs/04-systems-thinking-and-engineering-decisions.md) | How the subsystems interact, constraints, twelve "we chose X instead of Y because…" decisions with data, iteration cycles, risk table |
| Reproducibility and GitHub quality | [docs/05-reproducibility-build-and-test.md](docs/05-reproducibility-build-and-test.md) | Installation, running, tests without the car, round records, test plan, versioning |
| Journal | [docs/engineering-journal.md](docs/engineering-journal.md) | Timeline of the work and what we learned |
| History of the car | [docs/vehicle-history.md](docs/vehicle-history.md) | The eleven versions with photos |
| Rules | [docs/rules-compliance.md](docs/rules-compliance.md) | Rule by rule check of the vehicle and the repository |
| Releases | [CHANGELOG.md](CHANGELOG.md) | What changed in each version of the repository |

## 2. Repository structure

| Folder | Content |
| --- | --- |
| [`t-photos`](t-photos) | Team photos (official and funny) |
| [`v-photos`](v-photos) | Photos of the vehicle from every side, top and bottom |
| [`videos`](videos) | Links to the demonstration videos of each challenge |
| [`schemes`](schemes) | Wiring, power and flow diagrams (see the note in [02](docs/02-power-and-sensor-architecture.md#9-wiring-diagrams) about which one is current) |
| [`src`](src) | **The code of the vehicle**: the ROS 2 workspace that runs on the car (see [src/README.md](src/README.md)) |
| [`models`](models) | 3D-printed parts and chassis pieces (STL and previews) |
| [`tools`](tools) | Scripts to prepare the Pi, run a round, clean leftover nodes and calibrate the steering |
| [`docs`](docs) | The documentation described above |
| [`other`](other) | Extra material |

## 3. Meet the team!

<table width="100%">
  <tr>
    <td width="75%" style="padding: 20px;">
      <h3><strong>Isabella Gonzales 🌟</strong></h3>
      <b>🔧 Role: </b>Team Member<br>
      <b>💬 About me:</b> Hello! My name is Isabella, I'm 17 years old, and I love robotics. I founded Robotek Perú, a club where students can learn robotics and join competitions, and this is my second time at the WRO. My favorite hobbies are singing with my choir, practicing taekwondo, and art.<br>
      <b>🌐 Contact:</b> isabellamilagros842@gmail.com
    </td>
    <td align="center" width="25%" style="padding: 20px;">
      <img src="https://github.com/user-attachments/assets/4f37460a-c3a6-42cd-93e6-db632a62fead" width="800" style="border-radius: 10px;">
    </td>
  </tr>

  <tr>
    <td width="75%" style="padding: 20px;">
      <h3><strong>Rodrigo Osorio 6️⃣7️⃣</strong></h3>
      <b>🔧 Role: </b>Team Member<br>
      <b>💬 About me:</b> Hi. I'm Rodrigo, a 16-year-old teenager passionate about many kinds of knowledge across a wide variety of fields. This is my third time taking part of the World Robot Olympiad however, in the past I'd taken part of Robo Mission: Junior through the 2024 and 2025 seasons. Besides robotics, I'm thrilled about humanities, specially philosophy, a field where curiosity can be flow naturally. I'm excited to take part in this year's WRO season!!<br>
      <b>🌐 Contact:</b> rod10peru@gmail.com
    </td>
    <td align="center" width="25%" style="padding: 20px;">
      <img src="https://github.com/user-attachments/assets/c0f1333d-bda1-4e65-9402-9381d1af59e1" width="800" style="border-radius: 10px;">
    </td>
  </tr>

  <tr>
    <td width="75%" style="padding: 20px;">
      <h3><strong>Valeria Hurtado 🎷🐛</strong></h3>
      <b>🔧 Role: </b>Team Member<br>
      <b>💬 About me:</b> Hellooo! My name is Valeria and I’m 17 years old. I’m curious about science, technology, and how things work, which is what got me into robotics. This is my first time participating in the WRO, and I’m excited to figure things out along the way. Outside robotics, I enjoy baking, cycling, and designing things on Canva.<br>
      <b>🌐 Contact:</b> valeria.hurtado.delarosa@outlook.com
    </td>
    <td align="center" width="25%" style="padding: 20px;">
      <img src="https://github.com/user-attachments/assets/e68b56c1-9123-44ee-a194-316b82ebae8a" width="800" style="border-radius: 10px;">
    </td>
  </tr>

  <tr>
    <td width="75%" style="padding: 20px;">
      <h3><strong>Anthony Valladolid 🤓</strong></h3>
      <b>🔧 Role: </b>Coach<br>
      <b>💬 About me:</b> Hi, I am Anthony Valladolid, a Mechatronics Engineering graduate from Pontificia Universidad Católica del Perú, passionate about developing and researching emerging technologies. My main areas of interest are embedded systems, robotics, and applied artificial intelligence.<br>
      <b>🌐 Contact:</b> anthony.valladolid@pucp.edu.pe
    </td>
    <td align="center" width="25%" style="padding: 20px;">
      <img src="https://github.com/user-attachments/assets/2ce1a5c3-1f01-488f-a7aa-983ac89b57d3" width="800" style="border-radius: 10px;">
    </td>
  </tr>
</table>



## 4. The vehicle at a glance

| | |
| --- | --- |
| Name | **Sami** (version 11 of our car, 2024–2026) |
| Drive | Rear wheels, one Hiwonder 310 motor with encoder on the RRC Lite board, 1:1 gearing |
| Steering | Ackermann linkage, one 15 kg·cm servo, real wheel angle limited to 17.6° |
| Computer | Raspberry Pi 5 (Ubuntu 24.04, ROS 2 Jazzy) and Hiwonder RRC Lite (STM32F407) |
| Sensors | LDROBOT LD19 LiDAR, Pi camera with a wide lens, IMU of the RRC Lite, VL53L0X rear distance sensor |
| Power | Two 2S LiPo batteries: one for the electronics, one for the motor |
| Size | About 233 mm long and 147.6 mm wide (limits 300 × 200 mm); mass and height are recorded in [rules compliance](docs/rules-compliance.md) |


| Front | Left | Right |
| :--: | :--: | :--: | 
| <img src="https://github.com/user-attachments/assets/57818eb1-a1db-4454-9928-7ac42b46e3ae" width="90%" /> | <img src="https://github.com/user-attachments/assets/3c8d3351-0cf4-471f-be21-785de03897c0" width="90%" /> |  <img src="https://github.com/user-attachments/assets/b8d704a5-4bf8-4e6a-acd5-54b882e8ccc6" width="90%" /> |

| Back  | Top  | Bottom |
| :--: | :--: |:--: |  
| <img src="https://github.com/user-attachments/assets/1b9fdaee-b758-47dd-b572-509e3d5af35e" width="90%" /> | <img src="https://github.com/user-attachments/assets/19fba1bd-56ff-441b-8411-ddadb8295040" width="90%" /> |  <img src="https://github.com/user-attachments/assets/e8d83c7d-673f-43ad-bcc0-ec78e74bc9e3" width="90%" /> | 

More photos of the car and of its eleven versions are in [`v-photos`](v-photos) and in [docs/vehicle-history.md](docs/vehicle-history.md).

## 5. The two challenges and our strategy

**Open Challenge.** Three laps of a field whose inner walls change from round to round. `robotek_open` follows the walls with a LiDAR and detects each corner with the LiDAR; the corner turn is made at full lock until the heading is within 0.3 rad of the target and the controller takes over. See [docs/03](docs/03-software-architecture-and-obstacle-strategy.md#7-open-challenge).

**Obstacle Challenge.** Three laps with red and green signs, then parking in the lot. The car leaves the lot, follows a planned line with a side offset for each sign (red on the right, green on the left), plans each corner by driving candidate lines in a kinematic simulation, remembers every sign by its seat on the straights, recovers from contacts and stops when its servo does not follow. It then parks with a fixed manoeuvre closed on the LiDAR, the gyroscope and the rear sensor. The state machine, the perception that pairs LiDAR clusters with camera colours and the edge cases are in [docs/03](docs/03-software-architecture-and-obstacle-strategy.md). The flow diagrams of the first versions are in [`schemes`](schemes).

All decisions run in one 50 Hz loop; the camera and the LiDAR are slower, so the strategy always uses the newest data and stops the car if any sensor is stale. The strategy never talks to the hardware: `base_adapter` converts speed and wheel angle to motor and servo commands, so the same code runs in the simulator, in our honest lab and on the car.

## 6. How to build and run it

```bash
git clone https://github.com/ilovmangos/Robotek-WRO2026.git && cd Robotek-WRO2026
bash tools/setup-pi.sh                 # on the Raspberry Pi 5: ROS 2 Jazzy, dependencies, udev rules, colcon build
source install/setup.bash
bash tools/obstacle-round.sh           # Obstacle Challenge: start in the lot, three laps, partial park
bash tools/car-run.sh open             # Open Challenge
```

Wait for both board LEDs to turn **green** and press the board button **once**: it is the Start (a second press stops the car). Tests without the car, the lab and the round records are in [docs/05](docs/05-reproducibility-build-and-test.md).

## 7. Assembly instructions

### **Ackermann System**
+ To build the Ackermann system on the car, first screw the fixed parts that attach the system to the base.
+ Next, attach the two movable pieces that steer the wheels to the sides of the fixed part. Make sure these pieces can still rotate freely. Each of these pieces has two holes use the hole that is closer to the wheels.
+ Then, connect the wheel pieces with a linkage that has bearings on both ends. The bearings should be screwed into the other holes of the wheel pieces, forming a movable, half-rectangular structure.
+ Attach a second linkage, identical to the first but shorter, to one side of the system. This linkage connects to one of the holes on the wheel pieces, the same ones linked to the bearings of the first linkage. This shorter linkage will move the steering system and must be connected directly to the servo motor, which should be mounted vertically on the base.
+ Important: The servo’s output shaft and the side where the second linkage is attached should be on opposite sides.
Finally, attach the wheel hubs, the parts that hold the actual wheels, to the movable pieces via bearings. These bearings should allow the wheels to rotate freely.
 
### **Motor System**
+ Screw the motor mount, which is the piece that holds both the motor and its axle, onto the base. Then, screw the motor to this mount.
+ Insert the axle into the mount. The mount has two circular openings that the axle passes through. The axle should be supported by two bearings, which keep it centered, and two locking rings, which prevent side movement.
+ Once the axle is in place, connect the motor shaft and the axle using spacers, ensuring they do not collide with the motor screws.
 
### **Housings**
After both systems are assembled, install the housings on the top side of the base. Mount the camera, LiDAR, batteries, and Raspberry Pi according to the model layout:
+ The LiDAR housing goes at the front, ensuring its field of view is unobstructed.
+ The camera housing goes right behind the LiDAR housing, which it’s taller, so its view remains clear.
+ The battery and Raspberry Pi housings go behind them, forming a sort of ceiling above the servo motor that protrudes from the base.
 
### **Electronics**
1. Fix the Raspberry Pi 5 and the RRC Lite board in their housings and connect them with a USB cable (the board is the most critical USB device; keep it on its own controller).
2. Plug the LiDAR into the other controller and the camera ribbon into the Pi.
3. Connect the steering servo to **PWM port J4** of the RRC Lite and the drive motor to **port M2**; the motor battery goes to the motor supply and the electronics battery to the board input (see the diagram in [docs/02](docs/02-power-and-sensor-architecture.md#1-block-diagram-power-and-data)).
4. Wire the rear VL53L0X to the Pi: VIN to 3.3 V (pin 1), SDA to pin 3, SCL to pin 5, GND.
5. Copy the udev rules with `tools/setup-pi.sh`, check with the car on supports that the wheels follow the steering (`tools/steer_calibration.py`) and only then run a round.

## 8. Results and validation

Complete Obstacle rounds on the car (12 Nov 2026, the version in this repository):

| Round | Result |
| --- | --- |
| 00:02, no lot exit, no parking | 107.1 s from Start, laps 36.2 / 33.1 / 33.8 s, no recover manoeuvre; "perfect round" for the coach |
| 01:22, lot exit, three laps and partial park | 105.9 s to DONE, 19 of 19 signs passed on the right side, partial park at 29° |
| 02:39, parking-only test, CCW | 20.3 s, left parallel in the lot |

Honest simulation lab (LiDAR, gyroscope and camera only, with noise): 195 of 200 valid rounds without parking (mean 123.5 s) and 127 of 200 with parking. Points are **estimated** until a judge validates a round. Known limitation: parking in CW is not yet reliable. Details, dates and the test plan: [docs/05](docs/05-reproducibility-build-and-test.md).

## 9. Performance videos

| Challenge | Video |
| --- | --- |
| Obstacle Challenge (challenge 2) | [Watch on YouTube](https://youtu.be/lE8SPT6_tL0?si=ECjmNy6-T6QCe0LI) |
| Open Challenge (challenge 1) | [Watch on YouTube](https://youtu.be/DUVe36ZpR18?si=IGmmhTL5FZdeEi8m) |

The videos show the vehicle driving autonomously for more than 30 seconds, one for each challenge. They are also listed in [`videos`](videos).

## 10. Rules compliance, credits and licence

* Rule-by-rule check: [docs/rules-compliance.md](docs/rules-compliance.md).
* Credits (LiDAR driver, Hiwonder SDK, tools): [CREDITS.md](CREDITS.md).
* Licence: [MIT](LICENSE).
* Version history of this repository: [CHANGELOG.md](CHANGELOG.md).
