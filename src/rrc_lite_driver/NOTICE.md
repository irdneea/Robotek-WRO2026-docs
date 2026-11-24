# Provenance notice

Code based on Hiwonder MentorPi (https://github.com/Hiwonder/MentorPi, commit fb6d9969). It is included with Hiwonder's permission, confirmed by the author of this repository. The original code declares no licence; the changes of the Robotek team are under MIT.

Changes of the team with respect to MentorPi (`driver/ros_robot_controller`): names (`rrc_lite_driver`, node `rrc_driver`, topics `/rrc/...`), the steering servo (`SetAckerServoState` on `/rrc/acker_servo/set_state`, PWM servo channel selected with `acker_channel`), reconnection of the serial port, the serial port as a parameter (`port`, by default `/dev/rrc_lite` or `/dev/ttyACM0`) and retries with a clear message when the board is not plugged in. Only what the real car needs is included.
