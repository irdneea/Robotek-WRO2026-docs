# Rules compliance (WRO 2026 Future Engineers, General Rules of 15 Jan 2026)

| Rule | Requirement | Our vehicle | Status |
| --- | --- | --- | --- |
| 11.1 | ≤ 300 × 200 mm, 300 mm high | Outline about 233 mm long and 147.6 mm wide at the front wheels (CAD and caliper). Height to be measured with all parts | Length and width met; **height to measure** |
| 11.2 | ≤ 1.5 kg | To be weighed with batteries | **To measure before the final** |
| 11.3–11.5 | Four wheels, one driven axle, one steering actuator, no differential or omni wheels | Rear-wheel drive with one motor, Ackermann steering with one servo, ordinary wheels | Met |
| 11.6, 11.7 | Autonomous; no remote control or help | Starts with the board button and decides alone; no inputs after Start | Met |
| 11.10 | No Wi-Fi/Bluetooth/RF during rounds | The Raspberry Pi has Wi-Fi that we use for development only (SSH, live viewer). It must be **turned off** (`sudo rfkill block wifi bluetooth`) before the vehicle check; the code does not use it | **Checklist item** |
| 11.13 | At most two drive motors | One | Met |
| 11.17 | Only wired communication between electromechanical parts | USB, I²C, GPIO, CSI cables | Met |
| 9.9 | No sensor calibration before Start; no inputs choosing direction or mode | Gyro bias measured after Start; direction detected from the walls | Met |
| 7 | GitHub: README ≥ 5000 characters in English, ≥ 3 commits, photos, video ≥ 30 s per challenge, public | See the README | In progress |
| 3.3, 3.7 | Own work; no copied control program | Code by the team; the LD19 driver and the Hiwonder SDK are third-party and credited in [CREDITS.md](../CREDITS.md) | Met |
