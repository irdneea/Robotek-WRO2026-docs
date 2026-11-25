"""Servo and motor step tests on the real car, measured with the IMU and the LiDAR.

  ros2 launch robotek_bringup actuator_test.launch.py test:=servo|motor|steer|all

Waits for the board button, then runs a fixed plan of steps and writes
~/robotek-runs/<UTC>-actuator-<test>/ (commands.csv, imu.csv, scan.csv, plan.json,
summary.json; see actuator_analysis.py for what is measured):

  servo  car still (wheels on the ground or in the air): 0 -> +A -> 0 -> -A -> 0 for each
         angle. Only the servo moves.
  motor  straight ahead, servo centred: motor pulse at each % (<= 0.25 s), then 0 and the
         car coasts. Needs free_distance metres free in front (checked before each step).
  steer  servo to +-A first (settles for hold_time), then a 0.25 s motor pulse at steer_pct;
         the effective wheel angle is measured while the car rolls with the wheels already
         turned. (A servo step in the middle of a 0.25 s pulse was tried on 8 oct 2026: the car
         stops before the wheels finish turning and the gyro only shows vibration.) The servo
         delay comes from the 'servo' test.

The motor is never on for more than max_motor_time in a row: 0.25 s by default (user
request, 7 oct 2026), up to LONG_PULSE_LIMIT = 1 s only for pulses of at most
LONG_PULSE_MAX_PCT = 30 % (user allowed longer pulses at low power, 8 oct 2026, to measure
the cruise speed and the wheel angle). Enforced in tick(), whatever the plan says.

  ramp   for each target % in motor_pcts (up to RAMP_MAX_PCT): ramp_time at ramp_pct (30 %,
         which does not lift the nose), then ramp_hold at the target, then 0; the return is
         the same ramp in reverse. Starting straight at 40-60 % lifts the front wheels; the
         ramp is the user's proposal (8 oct 2026). A target above LONG_PULSE_MAX_PCT is only
         allowed right after the ramp step; the continuous pulse is at most RAMP_LIMIT s.

  cmdvel straight speeds through /cmd_vel (base_adapter applies the motor calibration and
         its accel/decel limits): for each speed in cmd_speeds (m/s, up to CMDVEL_MAX ~ 100 %
         motor; user allowed it with the ramps, 8 oct 2026) the command lasts v/cmd_accel
         (ramp up) + cmd_hold (steady, measured), then a long stop and the same back. Each
         speed needs v^2/2a + v*hold + v^2/2d + 0.5 m free ahead, checked before it runs; a
         speed without that room is skipped (and the faster ones too). While moving, an
         obstacle closer than stop_distance + 0.5 s * v publishes /robotek/estop (motor cut
         at once, no ramp).

  circle wheels fixed at each angle of circle_angles (both sides), then circle_pulses pulses
         of motor_time at steer_pct with stops in between (the car drives an arc), then the
         same pulses in reverse. Full scans go to scans.jsonl; actuator_analysis gets the arc
         radius from the LiDAR odometry and the gyro, and the wheel angle from it.

With return_back (default) every forward pulse is followed, after the stop, by a reverse
pulse with the same wheel angle, % and duration, so the car retraces the arc and ends
near where it started (needs free_back metres free behind; the rear cone is watched too).
This also exercises the reverse gear.

Safety: the plan only starts once the scan and the IMU are fresh (the LD19 takes a few
seconds to deliver data); the free-distance check needs a fresh scan. The motor is cut when the LiDAR sees anything closer than stop_distance in the
+-25 deg cone ahead, when the scan or the IMU go stale, at the end and on shutdown. Every
command is re-sent at 50 Hz (the team's motor node has no watchdog). Steering is limited
to +-25 deg like the strategies. Uses the servo directly (no base_adapter) and /motor_vel.
"""
import csv
import datetime
import json
import math
import os

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, LaserScan
from geometry_msgs.msg import Twist, Vector3
from std_msgs.msg import Bool, Float32

from .actuator_analysis import write_summary
from .mapping import ServoCalibration, servo_us

try:
    from rrc_lite_msgs.msg import BuzzerState, ButtonState, SetAckerServoState
except ImportError:  # only installed on the robot (HiWonder image)
    BuzzerState = ButtonState = SetAckerServoState = None

TICK = .02               # s, command rate
STALE = .5               # s without scan/IMU while the motor runs -> stop
SENSOR_WAIT = 30.        # s to wait for fresh scan and IMU before the plan starts
PRESS_STATES = (1, 5)    # board button press edges (as start_button)
STEER_LIMIT = 25.
MAX_MOTOR_ON = .25       # s, default limit on a continuous motor pulse
LONG_PULSE_LIMIT = 1.    # s, absolute ceiling (only at low power)
LONG_PULSE_MAX_PCT = 30. # %, highest motor command allowed in pulses over MAX_MOTOR_ON
RAMP_MAX_PCT = 60.       # %, highest target of the ramp test
RAMP_LIMIT = 1.2         # s, ramp + hold, continuous
CMDVEL_MAX = 1.3         # m/s in the cmdvel test (~100 % motor with robot.yaml)
# Wheelie: the car lifts its front at 100 % from standstill (8 oct 2026: pitch rate up to
# 1.8 rad/s, vertical accel down to -0.4 m/s^2; at 50 % 1.0 rad/s and >= 7.7 m/s^2, no lift).
# The board is turned 90 deg: pitch is gyro x. After a pulse that crosses either limit the
# remaining motor steps are skipped.
WHEELIE_PITCH = 1.3      # rad/s
WHEELIE_AZ = 5.          # m/s^2


class ActuatorTest(Node):
    def __init__(self):
        super().__init__('actuator_test')
        p = {k: self.declare_parameter(k, v).value for k, v in dict(
            test='servo', steer_angles=[10., 25.], motor_pcts=[15., 20., 30.], motor_time=MAX_MOTOR_ON,
            max_motor_time=MAX_MOTOR_ON, return_back=True, free_back=.6,
            ramp_pct=30., ramp_time=.5, ramp_hold=.7, ramp_free=1.5, cmd_speeds=[.15, .3],
            circle_angles=[25., 10.], circle_pulses=4, circle_sides='both',
            cmd_accel=1., cmd_decel=.6, cmd_hold=.6,
            steer_pct=30., coast_time=1.5, hold_time=1., free_distance=1.,
            stop_distance=.35, wait_button=True, run_dir='~/robotek-runs',
            servo_topic='/rrc/acker_servo/set_state', servo_duration=.02,
            servo_center_us=1500., servo_gain_pos=550./29., servo_gain_neg=500./29.,
            servo_sign=-1., servo_min_us=1000., servo_max_us=2050.).items()}
        self.p = p
        if SetAckerServoState is None:
            raise RuntimeError('rrc_lite_msgs missing: run this on the car')
        self.servo_cal = ServoCalibration(p['servo_center_us'], p['servo_gain_pos'], p['servo_gain_neg'],
                                          p['servo_sign'], p['servo_min_us'], p['servo_max_us'], STEER_LIMIT)
        self.servo_pub = self.create_publisher(SetAckerServoState, p['servo_topic'], 10)
        self.cmdvel = str(p['test']) == 'cmdvel'
        if self.cmdvel:
            self.twist_pub = self.create_publisher(Twist, '/cmd_vel', 10)
            self.estop_pub = self.create_publisher(Bool, '/robotek/estop', 10)
        else:
            self.motor_pub = self.create_publisher(Float32, '/motor_vel', 10)
        self.buzzer = self.create_publisher(BuzzerState, '/rrc/set_buzzer', 10)
        self.create_subscription(Imu, '/imu', self.on_imu, qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(ButtonState, '/rrc/button', self.on_button, 10)

        self.max_on = min(LONG_PULSE_LIMIT, float(p['max_motor_time']))
        self.pulse = min(self.max_on, float(p['motor_time']))
        if self.cmdvel:
            if max(abs(float(x)) for x in p['cmd_speeds']) > CMDVEL_MAX:
                raise RuntimeError(f'cmdvel: hasta {CMDVEL_MAX} m/s')
            a, h = float(p['cmd_accel']), float(p['cmd_hold'])
            self.max_on = max(abs(float(v))/a+h for v in p['cmd_speeds'])+.1
        if str(p['test']) == 'ramp':
            targets = [abs(float(x)) for x in p['motor_pcts']]
            if max(targets) > RAMP_MAX_PCT or abs(float(p['ramp_pct'])) > LONG_PULSE_MAX_PCT:
                raise RuntimeError(f'rampa: objetivo hasta {RAMP_MAX_PCT:.0f} %, escalon hasta '
                                   f'{LONG_PULSE_MAX_PCT:.0f} %')
            self.max_on = min(RAMP_LIMIT, float(p['ramp_time'])+float(p['ramp_hold']))
        elif self.pulse > MAX_MOTOR_ON:
            pcts = list(p['motor_pcts'])+[p['steer_pct']]
            if max(abs(float(x)) for x in pcts) > LONG_PULSE_MAX_PCT:
                raise RuntimeError(f'pulsos de {self.pulse:.2f} s solo hasta {LONG_PULSE_MAX_PCT:.0f} %')
        self.plan = self.build_plan(str(p['test']))
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.run_dir = os.path.join(os.path.expanduser(p['run_dir']), f"{stamp}-actuator-{p['test']}")
        os.makedirs(self.run_dir, exist_ok=True)
        with open(os.path.join(self.run_dir, 'plan.json'), 'w') as f:
            json.dump(dict(params=p, plan=self.plan), f, indent=2)
        self.files = {name: open(os.path.join(self.run_dir, f'{name}.csv'), 'w', newline='')
                      for name in ('commands', 'imu', 'scan')}
        self.csv = {name: csv.writer(f) for name, f in self.files.items()}
        self.csv['commands'].writerow(['t', 'step', 'phase', 'servo_deg', 'servo_us', 'motor_pct'])
        self.csv['imu'].writerow(['t', 'gx', 'gy', 'gz', 'ax', 'ay', 'az'])
        self.csv['scan'].writerow(['t', 'front', 'front_min', 'back', 'back_min'])
        self.full_scans = open(os.path.join(self.run_dir, 'scans.jsonl'), 'w') \
            if str(p['test']) == 'circle' else None

        self.imu_t = self.scan_t = None
        self.pitch_max, self.az_min = 0., 99.
        self.wheelie = None
        self.skip_return = False
        self.front = self.front_min = math.inf
        self.back = self.back_min = math.inf
        self.started = not p['wait_button']
        self.ready = False
        self.wait_since = None
        self.index = -1
        self.step_end = None
        self.command = (0., 0.)
        self.motor_since = None
        self.pulse_cut = False
        self.finished = False
        self.done_at = None
        self.create_timer(TICK, self.tick)
        self.get_logger().info(f"Prueba '{p['test']}': {len(self.plan)} pasos, datos en {self.run_dir}. "
                               + ('Pulsa el boton de la placa para empezar.' if p['wait_button'] else ''))

    # ------------------------------------------------------------------ plan
    def build_plan(self, test):
        p = self.p
        angles = [min(STEER_LIMIT, abs(float(a))) for a in p['steer_angles']]
        plan = [dict(step='inicio', phase='idle', servo=0., motor=0., time=1.)]
        if test in ('servo', 'all'):
            for a in angles:
                for target in (a, 0., -a, 0.):
                    plan.append(dict(step=f'servo {target:+.0f}', phase='servo', servo=target, motor=0.,
                                     time=p['hold_time']))
        back = bool(p['return_back'])

        def return_steps(servo, pct):
            if not back:
                return []
            return [dict(step=f'volver {servo:+.0f}', phase='return', servo=servo, motor=-pct,
                         time=self.pulse, needs_back=p['free_back']),
                    dict(step='parar', phase='return', servo=servo, motor=0., time=1.5)]

        if test in ('motor', 'all'):
            for pct in p['motor_pcts']:
                plan.append(dict(step=f'motor {pct:.0f}%', phase='motor', servo=0., motor=float(pct),
                                 time=self.pulse, needs_free=p['free_distance']))
                plan.append(dict(step='motor 0', phase='motor', servo=0., motor=0., time=2.))
                plan += return_steps(0., float(pct))
        if test == 'circle':
            angles = [min(STEER_LIMIT, abs(float(a))) for a in p['circle_angles']]
            pct = float(p['steer_pct'])
            sides = {'left': (1.,), 'right': (-1.,), 'both': (1., -1.)}[str(p['circle_sides'])]
            for a in angles:
                for side in (sign*a for sign in sides):
                    plan.append(dict(step=f'ruedas a {side:+.0f}', phase='circle_pre', servo=side, motor=0.,
                                     time=p['hold_time']))
                    for k in range(int(p['circle_pulses'])):
                        plan += [dict(step=f'circulo {side:+.0f} pulso {k+1}', phase='circle', servo=side,
                                      motor=pct, time=self.pulse, needs_free=.6),
                                 dict(step=f'circulo {side:+.0f} pausa', phase='circle', servo=side, motor=0.,
                                      time=1.)]
                    if back:
                        for k in range(int(p['circle_pulses'])):
                            plan += [dict(step=f'volver {side:+.0f} pulso {k+1}', phase='return', servo=side,
                                          motor=-pct, time=self.pulse, needs_back=p['free_back']),
                                     dict(step='parar', phase='return', servo=side, motor=0., time=1.)]
                    plan.append(dict(step='centrar', phase='circle_post', servo=0., motor=0., time=1.))
        if test == 'cmdvel':
            a, d, h = float(p['cmd_accel']), float(p['cmd_decel']), float(p['cmd_hold'])
            for v in p['cmd_speeds']:
                v = float(v)
                room = v*v/(2*a)+v*h+v*v/(2*d)+.5
                stop = v/d+1.5
                plan += [dict(step=f'acelerar a {v:.2f} m/s', phase='ramp', servo=0., motor=v,
                              time=v/a, needs_free=room, speed=v),
                         dict(step=f'cmd_vel {v:.2f} m/s', phase='motor', servo=0., motor=v, time=h, speed=v),
                         dict(step='cmd_vel 0', phase='motor', servo=0., motor=0., time=stop)]
                if back:
                    plan += [dict(step=f'volver a {v:.2f} m/s', phase='return', servo=0., motor=-v,
                                  time=v/a+h, needs_back=p['free_back'], speed=v),
                             dict(step='parar', phase='return', servo=0., motor=0., time=stop)]
        if test == 'ramp':
            r, ramp_time, hold = float(p['ramp_pct']), float(p['ramp_time']), float(p['ramp_hold'])
            for pct in p['motor_pcts']:
                pct = float(pct)
                plan += [dict(step=f'rampa {r:.0f}%', phase='ramp', servo=0., motor=r, time=ramp_time,
                              needs_free=p['ramp_free']),
                         dict(step=f'motor {pct:.0f}%', phase='motor', servo=0., motor=pct, time=hold,
                              after_ramp=True),
                         dict(step='motor 0', phase='motor', servo=0., motor=0., time=2.)]
                if back:
                    plan += [dict(step=f'volver rampa {r:.0f}%', phase='return', servo=0., motor=-r,
                                  time=ramp_time, needs_back=p['free_back']),
                             dict(step=f'volver {pct:.0f}%', phase='return', servo=0., motor=-pct,
                                  time=hold, after_ramp=True),
                             dict(step='parar', phase='return', servo=0., motor=0., time=1.5)]
        if test in ('steer', 'all'):
            for a in angles:
                for side in (a, -a):
                    pct = float(p['steer_pct'])
                    plan += [dict(step=f'ruedas a {side:+.0f}', phase='turn_pre', servo=side, motor=0.,
                                  time=p['hold_time']),
                             dict(step=f'giro {side:+.0f}', phase='turn', servo=side, motor=pct,
                                  time=self.pulse, needs_free=p['free_distance']),
                             dict(step=f'giro {side:+.0f} sin motor', phase='turn_coast', servo=side,
                                  motor=0., time=p['coast_time']),
                             *return_steps(side, pct),
                             dict(step='centrar', phase='turn_post', servo=0., motor=0., time=1.)]
        plan.append(dict(step='fin', phase='idle', servo=0., motor=0., time=.5))
        if len(plan) == 2:
            raise RuntimeError("test must be servo, motor, steer, all, ramp, cmdvel or circle")
        # Above LONG_PULSE_MAX_PCT only as the second step of a ramp (never from standstill).
        for previous, step in zip(plan, plan[1:]):
            if abs(step['motor']) > LONG_PULSE_MAX_PCT and step['time'] > MAX_MOTOR_ON:
                ok = step.get('after_ramp') and previous['phase'] in ('ramp', 'return') \
                    and 0. < abs(previous['motor']) <= LONG_PULSE_MAX_PCT
                if not ok:
                    raise RuntimeError(f"{step['step']}: mas de {LONG_PULSE_MAX_PCT:.0f} % solo tras la rampa")
        return plan

    # --------------------------------------------------------------- sensors
    def now(self):
        return self.get_clock().now().nanoseconds*1e-9

    def on_imu(self, msg):
        self.imu_t = self.now()
        g, a = msg.angular_velocity, msg.linear_acceleration
        # Only while the motor pushes forward: stopping (our driver brakes by reversing for
        # 0.12 s) also jolts the chassis and once tripped this check at 50 % (8 oct 2026).
        if self.command[1] > 0.:
            self.pitch_max = max(self.pitch_max, abs(g.x))
            self.az_min = min(self.az_min, a.z)
        self.csv['imu'].writerow([f'{self.imu_t:.4f}', g.x, g.y, g.z, a.x, a.y, a.z])

    def on_scan(self, msg):
        """Scan with 0 rad ahead (scan_adapter): median ahead and closest in the +-25 deg cone."""
        self.scan_t = self.now()
        r = np.asarray(msg.ranges, float)
        a = np.arctan2(np.sin(msg.angle_min+np.arange(r.size)*msg.angle_increment),
                       np.cos(msg.angle_min+np.arange(r.size)*msg.angle_increment))
        ok = np.isfinite(r) & (r > max(msg.range_min, .05))
        ahead = ok & (np.abs(a) < math.radians(10.))
        cone = ok & (np.abs(a) < math.radians(25.))
        self.front = float(np.median(r[ahead])) if ahead.any() else math.inf
        self.front_min = float(r[cone].min()) if cone.any() else math.inf
        behind = ok & (np.abs(a) > math.radians(170.))
        rear = ok & (np.abs(a) > math.radians(155.))
        self.back = float(np.median(r[behind])) if behind.any() else math.inf
        self.back_min = float(r[rear].min()) if rear.any() else math.inf
        self.csv['scan'].writerow([f'{self.scan_t:.4f}', self.front, self.front_min, self.back, self.back_min])
        if self.full_scans is not None:
            self.full_scans.write(json.dumps(dict(
                t=round(self.scan_t, 4), angle_min=msg.angle_min, angle_increment=msg.angle_increment,
                range_min=msg.range_min, ranges=[round(x, 4) if math.isfinite(x) else None for x in msg.ranges]))+'\n')

    def on_button(self, msg):
        if msg.state in PRESS_STATES and not self.started and not self.finished:
            self.started = True
            self.beep(1)
            self.get_logger().info('Empieza la prueba.')

    def beep(self, repeat):
        beep = BuzzerState()
        beep.freq, beep.on_time, beep.off_time, beep.repeat = 1500, .08, .08, repeat
        self.buzzer.publish(beep)

    # -------------------------------------------------------------- commands
    def send(self, servo_deg, motor_pct):
        if self.cmdvel:   # motor_pct is a speed in m/s here; base_adapter drives servo and motor
            self.twist_pub.publish(Twist(linear=Vector3(x=float(motor_pct))))
            return int(self.p['servo_center_us'])
        servo_deg = max(-STEER_LIMIT, min(STEER_LIMIT, servo_deg))
        us = int(round(servo_us(math.radians(servo_deg), self.servo_cal)))
        command = SetAckerServoState()
        command.position, command.duration = us, float(self.p['servo_duration'])
        self.servo_pub.publish(command)
        self.motor_pub.publish(Float32(data=float(motor_pct)))
        return us

    def log_command(self, step, us):
        servo_deg, motor = self.command
        self.csv['commands'].writerow([f'{self.now():.4f}', step['step'], step['phase'],
                                       servo_deg, us, motor])

    def abort(self, reason):
        if self.cmdvel and self.command[1] != 0.:
            self.estop_pub.publish(Bool(data=True))   # cut the motor now, no soft ramp
        self.get_logger().error(f'Prueba detenida: {reason}')
        with open(os.path.join(self.run_dir, 'ABORTED.txt'), 'w') as f:
            f.write(reason+'\n')
        self.finish()

    def finish(self):
        if self.finished:
            return
        self.finished = True
        if self.full_scans is not None:
            self.full_scans.flush()
        self.done_at = self.now()+.5      # keep sending zeros a little longer, then exit
        self.command = (0., 0.)
        for _ in range(3):
            self.send(0., 0.)
        for f in self.files.values():
            f.flush()
        self.beep(2)
        try:
            summary = write_summary(self.run_dir)
            for row in summary['steps']:
                self.get_logger().info(json.dumps(row, ensure_ascii=False))
        except Exception as error:  # noqa: BLE001 - keep the data even if the analysis fails
            self.get_logger().error(f'Analisis fallido ({error}); datos en {self.run_dir}')
        self.get_logger().info(f'Fin. Resumen en {self.run_dir}/summary.json')

    def tick(self):
        if self.finished:
            self.send(0., 0.)
            return
        now = self.now()
        if not self.started:
            self.send(0., 0.)
            return
        if not self.ready:
            self.send(0., 0.)
            self.wait_since = self.wait_since or now
            if self.fresh('scan', now) and self.fresh('imu', now):
                self.ready = True
                self.get_logger().info(f'Sensores listos ({now-self.wait_since:.1f} s); '
                                       f'{self.front:.2f} m libres delante.')
            elif now-self.wait_since > SENSOR_WAIT:
                self.abort('el LiDAR o la IMU no publican')
            return
        # Cut one tick early so the pulse never exceeds MAX_MOTOR_ON (ticks are TICK apart).
        if self.command[1] != 0. and now-self.motor_since >= self.max_on-TICK:
            self.command = (self.command[0], 0.)
            self.motor_since, self.pulse_cut = None, True
            self.log_command(dict(self.plan[self.index], step=f'corte {self.max_on} s'),
                             self.send(*self.command))
        if self.step_end is None or now >= self.step_end:
            self.index += 1
            if self.index >= len(self.plan):
                self.finish()
                return
            step = self.plan[self.index]
            if self.wheelie is None and (self.pitch_max > WHEELIE_PITCH or self.az_min < WHEELIE_AZ):
                self.wheelie = (f'el morro se levanto (cabeceo {self.pitch_max:.2f} rad/s, '
                                f'az min {self.az_min:.1f} m/s2)')
                self.get_logger().warn(self.wheelie+': no se sube mas el motor.')
            self.pitch_max, self.az_min = 0., 99.
            skip = (self.wheelie and step['motor'] > 0.) or (self.skip_return and step['motor'] < 0.)
            if skip:
                # A skipped forward pulse also skips its return; a pulse that ran keeps it.
                if step['motor'] > 0.:
                    self.skip_return = True
                self.get_logger().info(f"{step['step']}: omitido ({self.wheelie})")
                self.step_end = now
                return
            if step['motor'] > 0.:
                self.skip_return = False
            needs = step.get('needs_free')
            if needs and not self.fresh('scan', now):
                self.abort(f"{step['step']}: sin scan reciente para comprobar el espacio libre")
                return
            if needs and self.front < needs:
                if self.cmdvel:   # not enough room for this speed: stop the series here
                    self.abort(f"{step['step']}: solo {self.front:.2f} m libres delante "
                               f"(hacen falta {needs:.2f} m para esa velocidad)")
                else:
                    self.abort(f"{step['step']}: solo {self.front:.2f} m libres delante (hacen falta {needs} m)")
                return
            needs_back = step.get('needs_back')
            if needs_back and not self.fresh('scan', now):
                self.abort(f"{step['step']}: sin scan reciente para comprobar el espacio detras")
                return
            if needs_back and self.back < needs_back:
                self.abort(f"{step['step']}: solo {self.back:.2f} m libres detras (hacen falta {needs_back} m)")
                return
            motor = step['motor']
            if motor == 0.:
                self.motor_since, self.pulse_cut = None, False
            elif self.pulse_cut:
                motor = 0.                    # the pulse was cut: no new one until a 0 step
            elif self.motor_since is None:
                self.motor_since = now
            self.command = (step['servo'], motor)
            self.step_end = now+step['time']
            self.log_command(step, self.send(*self.command))
            self.get_logger().info(f"{step['step']} ({step['time']:.1f} s)")
            return
        limit = self.p['stop_distance']
        if self.cmdvel:
            limit += .5*abs(self.command[1])   # m/s: half a second of travel more
        if self.command[1] > 0. and self.front_min < limit:
            self.abort(f'obstaculo a {self.front_min:.2f} m delante')
            return
        if self.command[1] < 0. and self.back_min < self.p['stop_distance']:
            self.abort(f'obstaculo a {self.back_min:.2f} m detras')
            return
        if self.command[1] != 0.:
            for name, t in (('LiDAR', self.scan_t), ('IMU', self.imu_t)):
                if t is None or now-t > STALE:
                    self.abort(f'sin datos de {name}')
                    return
        self.send(*self.command)

    def fresh(self, sensor, now):
        t = self.scan_t if sensor == 'scan' else self.imu_t
        return t is not None and now-t < STALE

    def close(self):
        self.finish()
        for f in self.files.values():
            f.close()
        if self.full_scans is not None:
            self.full_scans.close()


def main(args=None):
    rclpy.init(args=args)
    node = ActuatorTest()
    try:
        while rclpy.ok() and (node.done_at is None or node.now() < node.done_at):
            rclpy.spin_once(node, timeout_sec=.05)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        rclpy.try_shutdown()
