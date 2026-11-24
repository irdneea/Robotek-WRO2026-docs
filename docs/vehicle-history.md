# Vehicle history: eleven versions of the car

This page keeps the evolution of the car (versions 1–11, 2024–2026) that used to live in the README. The *current* car and the reasons behind each change are documented in [01 Mobility](01-mobility-and-mechanical-design.md), [02 Power and sensors](02-power-and-sensor-architecture.md) and [04 Decisions](04-systems-thinking-and-engineering-decisions.md). Where an older description below contradicts them (for example the motor driver), the numbered documents are the authoritative ones; the motor driver history is summarised in the table at the end of this page.

### **<ins>General Description of the Car</ins>**
Our autonomous vehicle is built to take on both the Open and Obstacle Challenges at the Future Engineers competition. Running on Ubuntu with ROS, it can process information and make decisions in real time. The car uses an Ackermann steering system and a custom-built chassis to move smoothly through turns and straight paths. A LiDAR sensor helps it detect the field walls, while the camera identifies traffic signs and obstacles. With this setup, the car can adapt its route, count laps, and complete the course efficiently.
<br>

| Front | Left | Right |
| :--: | :--: | :--: | 
| <img src="https://github.com/user-attachments/assets/57818eb1-a1db-4454-9928-7ac42b46e3ae" width="90%" /> | <img src="https://github.com/user-attachments/assets/3c8d3351-0cf4-471f-be21-785de03897c0" width="90%" /> |  <img src="https://github.com/user-attachments/assets/b8d704a5-4bf8-4e6a-acd5-54b882e8ccc6" width="90%" /> |

| Back  | Top  | Bottom |
| :--: | :--: |:--: |  
| <img src="https://github.com/user-attachments/assets/1b9fdaee-b758-47dd-b572-509e3d5af35e" width="90%" /> | <img src="https://github.com/user-attachments/assets/19fba1bd-56ff-441b-8411-ddadb8295040" width="90%" /> |  <img src="https://github.com/user-attachments/assets/e8d83c7d-673f-43ad-bcc0-ec78e74bc9e3" width="90%" /> | 
> [!NOTE]
> 📸 Visit our [`v-photos`](../v-photos) folder for more detailed photos of the car



### **<ins>Versions of the Car</ins>**
Our vehicle has gone through **10 versions** (and since we are always improving, there are still more to come). It all started with a cardboard prototype, then moved on to acrylic and metal chassis designs, and later, we made personalized adjustments to a HiWonder kit. Along the way, we also experimented with different wheel designs, repositioned components, tested sensors like LiDAR, and finally adopted a new operating environment with ROS and Ubuntu.

<table>  
  <tr>
    <th width="10%">Version</th>
    <th width="40%">Car Photo</th>
    <th width="50%">Description</th>
  </tr>
  
  <!-- Version 1 -->
  <tr>
    <td align="center"><i>Version N°1</i></td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/88cb9f71-715d-41d5-8dcd-54870af7fa87" width="330"height="230"/>
    </td>
    <td>
      We built a cardboard prototype to test and understand the Ackermann steering system and wheel movement. This served as a reference to learn about the placement of components and systems.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-1">➡️ See more photos 🚗</a>
    </td>
  </tr>

  <!-- Version 2 -->
  <tr>
    <td align="center"><i>Version N°2</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/14afa30d-317e-43f8-b6ef-d63897212c88" width="330" height="230"/>
    </td>
    <td>
      <br>We cut and incorporated an acrylic chassis and designed/3D-printed housing pieces for the camera, Ackermann system, and other components. The Ackermann used a stepper motor, and to perceive its surroundings, the car relied on infrared sensors and a webcam. 
      <br><br>The main controllers were a Raspberry Pi 4 and an Arduino Nano, powered by a power bank and lithium batteries. The car’s movement was driven by a single motor.<br><br> 
      <a href="../v-photos/vehicle-versions/README.md#version-2">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 3 -->
  <tr>
    <td align="center"><i>Version N°3</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/5299a922-0fb3-43a8-9a32-9bdbc77225d7" width="330" height="230"/>
    </td>
    <td>
      <br> We replaced the power bank with a smaller one, adjusted component placement into a two-level car system, and installed new wheels. Lithium batteries were replaced with higher-current ones, and the infrared sensors were moved to the front, so the vehicle could make more precise turns.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-3">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 4 -->
  <tr>
    <td align="center"><i>Version N°4</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/80568426-a136-48a6-b219-9c05dd3e2584" width="330" height="230"/>
    </td>
    <td>
    <br> We upgraded the chassis to a modified HiWonder Kit and replaced the infrared sensors with a LiDAR for more accurate obstacle detection. The webcam was also switched to a monocular camera. The original car motor was replaced by two encoder motors, adapted with gears to drive a single wheel in compliance with competition guidelines.<br><br>

For the Ackermann steering, we replaced the stepper motor with a servomotor. On top of that, we moved away from the Arduino Nano and began implementing the ROS framework.<br><br>
<a href="../v-photos/vehicle-versions/README.md#version-4">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 5 -->
  <tr>
    <td align="center"><i>Version N°5</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/fe6757a1-3fe5-4b12-b856-bedcc28a5b50" width="330" height="230"/>
    </td>
    <td>
      <br>Our main improvement was the chassis. We joined the two bases by drilling them together and carefully organized the components with the Raspberry Pi inside. The LiDAR was placed on top so nothing would block its view, and we also completed and installed the camera housing.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-5">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 6 -->
  <tr>
    <td align="center"><i>Version N°6</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/7e483e4c-2f35-48e9-8125-00a2123f06a2" width="330" height="230"/>
    </td>
    <td>
      <br> Wheels were changed to adjust the car’s height so the Lidar could detect walls within the 10 cm range (previously it was too high and failed). The housing material was upgraded from PLA to polycarbonate for greater resistance, and the Open Challenge (autonomous 3 rounds driving) was completed.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-6">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 7 -->
  <tr>
    <td align="center"><i>Version N°7</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/105155b6-ddb2-4885-aa63-7e07f1468315" width="330" height="230"/>
    </td>
    <td>
      <br> Using our HiWonder kit as the base, we designed and cut a completely new, smaller chassis with personalized mounting holes for all components, new housing pieces were created, and the two-motor system was replaced by a single motor in a gear system.<br><br>
    We also moved from a two-level structure to a single-level layout, placing all the components on the same surface to give the Raspberry Pi better airflow and easier access. The car successfully detected and avoided the first traffic signs.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-7">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 8 -->
  <tr>
    <td align="center"><i>Version N°8</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/5d66a0cd-a12c-4155-ae6f-aa4655cf6e0e" width="330" height="250"/>
    </td>
    <td>
      <br> <b>Car dimensions:</b> 15 x 23 cm <br><br>
      We 3D-printed new, slimmer front wheels because the original ones stuck out too much from the chassis. A custom housing was also printed for the batteries, and most importantly, the Ackermann steering servo was mounted vertically to save space and allow for a wider turning angle.<br><br>
During previous testing, we realized the LiDAR was struggling to properly detect the walls of the field, so we 3D-printed and implemented a small angled mount to give it a slight tilt.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-8">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

<!-- Version 9 -->
  <tr>
    <td align="center"><i>Version N°9</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/312c2e7e-4638-4917-b54a-fff2bb1a2965" width="330" height="450"/>
    </td>
    <td>
      <br> <b>Car dimensions:</b> 15 x 20 cm <br><br>
In this version, the components were arranged more efficiently to save space. We added a custom housing for the batteries, placed the Pi5 controller on top, and mounted the Raspberry above it, creating a layered system.<br><br> 
A new chassis base was printed in MDF, and the Ackermann was moved slightly because, in the previous version, the rack was colliding with the servo. To improve traction, we added a groove to the wheels and printed small cylinders between them to prevent contact with the screws. With these adjustments, the robot managed to complete a lap in <b>20 seconds</b>.<br><br>
      <a href="../v-photos/vehicle-versions/README.md#version-9">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 10 -->
  <tr>
    <td align="center"><i>Version N°10</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/03a1e68f-fcf6-40c0-91ea-beff7a2833ab" width="330" height="450"/>
    </td>
    <td>
      <br> <b>Car dimensions:</b> 15 x 18 x 16 cm <br><br> 
We removed the LiDAR housing because, after testing the robot multiple times, we found that vision worked better without it. We also printed the rear wheels, so now all wheels are the same. We modified the gear system, which allowed the robot to complete the 3 laps faster. It now takes less than 10 seconds to complete an entire lap, and it manages to complete the 3 laps in 28 seconds. The small and big gears were interchanged so that the big gear is directly attached to the motor shaft
<br><br>
  <a href="../v-photos/vehicle-versions/README.md#version-10">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>

  <!-- Version 11 -->
  <tr>
    <td align="center"><i>Version N°11</i></td>
    <td align="center"><img src="https://github.com/user-attachments/assets/deba8088-32d4-4846-b635-17d4c11e2836" width="330" height="450"/>
    </td>
    <td>
      <br> <b>Car dimensions:</b> N x N x N cm <br><br> 
We noticed that the room lights were affecting our color detection, so we added a 16-LED WS2812 RGB ring light (5V) to keep the lighting consistent. We also moved the LiDAR again. We printed a new housing and placed it at the front, right under the chassis, an adjustment that significantly improved wall detection.
Finally, we replaced the old L298N motor driver with a TB6612FNG. This made a big difference because we can now control the speed more smoothly, starting at around 35%, and we have much better control when reversing and stopping.
<br><br>
  <a href="../v-photos/vehicle-versions/README.md#version-10">➡️ See more photos 🚗</a><br><br>
    </td>
  </tr>
  
</table>


<br>

> [!NOTE]
> 🌱 Visit our [`vehicle-versions`](../v-photos/vehicle-versions/README.md) folder to see photos and videos of our car evolution.

<br>

## Motor driver history (what the table above does not say)

| Period | Driver | Why it changed |
| --- | --- | --- |
| 2024 – Oct 2026 | L298N, then TB6612FNG on the Raspberry Pi GPIO | The TB6612FNG allowed smooth speeds from about 35 % PWM and reliable reversing; the L298N stalled at 50 % or less. |
| 8 Oct 2026 | TB6612FNG, standby pin GPIO13 | The motor "worked only sometimes": a software bug (the standby pin was never raised by our node) and a PWM write that `lgpio` ignored. Both fixed and verified with the car in the air. |
| From 1 Nov 2026 | RRC Lite board, motor port M2 (since 4 Nov), closed-loop speed from the motor encoder (`rrc_lite_driver`) | The board holds the commanded speed itself, so the strategies ask for m/s and stop being sensitive to battery sag. See [01 Mobility](01-mobility-and-mechanical-design.md). |
