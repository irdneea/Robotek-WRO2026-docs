"""Tests of every function of the RRC Lite board, one after the other, on the car.

  # the team's stack stopped (~/scripts/stop_ros.py) and the board node alone:
  source ~/wro_controller_ws/install/setup.bash && source ~/Projects/WRO-Strategies/install/setup.bash
  ros2 run rrc_lite_driver rrc_driver &
  ros2 run robotek_hardware rrc_test                                  # safe tests only
  ros2 run robotek_hardware rrc_test --ros-args -p tests:="[imu,battery,buzzer]"
  ros2 run robotek_hardware rrc_test --ros-args -p tests:="[all]" -p wheels_in_air:=true

Writes ~/robotek-runs/<UTC>-rrc-test/results.json and summary.txt. Statuses: PASS / WARN / FAIL
(checked here), INFO (measured), MANUAL (a person looks or listens: buzzer, LEDs, OLED) and
SKIP. Plan, expected values and what each test shows: docs/rrc-lite-pruebas.md.

Safe tests (default, nothing moves): topics, enable, battery, imu, button, buzzer, led, rgb,
oled, joy, sbus. The car must be still for `imu`.
Tests that move something are never in the default list and need wheels_in_air:=true (the
car lifted, wheels free) or an explicit parameter:
  acker_servo   steering servo through the team's acker_servo/set_state: 0 -> +10 -> 0 -> -10 -> 0
  pwm_servo     PWM servos `pwm_ids` (default none) +-pwm_delta us around 1500 and back
  pwm_read      reads position/offset of `pwm_ids` (the official SDK waits forever without an
                answer: if the board does not reply, restart the board node)
  bus_read      reads the bus servos `bus_ids` (same warning)
  board_motor   the board's own motor ports `motor_ids` at motor_rps for motor_time s each
                (the car's motor is the Pi's TB6612, not these ports)
Motors are re-sent at 50 Hz while on, set to 0 at the end, on error and on Ctrl+C.
"""
import datetime
import json
import math
import os
import threading
import time

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, Joy
from std_msgs.msg import Bool, UInt16

from .mapping import ServoCalibration, servo_us
from .rrc_analysis import battery_report, button_report, imu_report, rate_hz, stats, topic_report

try:
    from rrc_lite_msgs.msg import (ButtonState, BuzzerState, LedState, MotorsState, MotorState,
                                               OLEDState, PWMServoState, RGBState, RGBStates, Sbus,
                                               SetPWMServoState)
    from rrc_lite_msgs.srv import GetBusServoState, GetPWMServoState
    from rrc_lite_msgs.msg import GetBusServoCmd, GetPWMServoCmd
except ImportError:  # only on the robot (HiWonder image)
    ButtonState = None
try:
    from rrc_lite_msgs.msg import SetAckerServoState   # the team's fork
except ImportError:
    SetAckerServoState = None

SAFE = ['topics', 'enable', 'battery', 'imu', 'button', 'buzzer', 'led', 'rgb', 'oled', 'joy', 'sbus']
MOVING = ['acker_servo', 'pwm_servo', 'pwm_read', 'bus_read', 'board_motor']
SERVO_TEST_DEG = 10.     # far below the 25 deg limit
MAX_MOTOR_RPS = 0.5      # 0.5 rps with 67 mm wheels = 0.1 m/s
MAX_MOTOR_TIME = 1.0
RGB_LEVEL = 40           # of 255: the LED strip at 100 % browned the Pi out (8 oct 2026)


class RrcTest(Node):
    def __init__(self):
        super().__init__('rrc_test')
        p = {k: self.declare_parameter(k, v).value for k, v in dict(
            ns='/rrc', tests=['safe'], wheels_in_air=False, run_dir='~/robotek-runs',
            imu_seconds=4., battery_seconds=8., button_timeout=20., listen_seconds=3.,
            pwm_ids=[0], pwm_delta=100, led_ids=[1, 2, 3], bus_ids=[0], motor_ids=[0], motor_rps=0.3, motor_time=0.5,
            service_timeout=2.).items()}
        self.p = p
        self.ns = p['ns'].rstrip('/')
        self.pwm_ids = [int(i) for i in p['pwm_ids'] if int(i) > 0]
        self.bus_ids = [int(i) for i in p['bus_ids'] if int(i) > 0]
        self.motor_ids = [int(i) for i in p['motor_ids'] if int(i) > 0] or [1, 2, 3, 4]
        self.motor_rps = max(-MAX_MOTOR_RPS, min(MAX_MOTOR_RPS, float(p['motor_rps'])))
        self.motor_time = max(0.1, min(MAX_MOTOR_TIME, float(p['motor_time'])))
        self.lock = threading.Lock()
        self.imu, self.battery, self.buttons, self.joy, self.sbus = [], [], [], [], []
        self.collect = set()
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.dir = os.path.join(os.path.expanduser(p['run_dir']), f'{stamp}-rrc-test')
        os.makedirs(self.dir, exist_ok=True)
        self.results = {}
        self.t0 = time.time()
        self.setup_io()

    def topic(self, name):
        return f'{self.ns}/{name}'

    def setup_io(self):
        self.create_subscription(Imu, self.topic('imu_raw'), self.on_imu, qos_profile_sensor_data)
        self.create_subscription(UInt16, self.topic('battery'), self.on_battery, 10)
        self.create_subscription(Joy, self.topic('joy'), lambda m: self.add('joy', self.joy, (m.axes, m.buttons)), 10)
        self.enable_pub = self.create_publisher(Bool, self.topic('enable_reception'), 1)
        if ButtonState is None:
            return
        self.create_subscription(ButtonState, self.topic('button'),
                                 lambda m: self.add('button', self.buttons, (m.id, m.state)), 10)
        self.create_subscription(Sbus, self.topic('sbus'),
                                 lambda m: self.add('sbus', self.sbus, tuple(m.channel)), 10)
        pub = lambda msg, name: self.create_publisher(msg, self.topic(name), 10)
        self.buzzer_pub, self.led_pub = pub(BuzzerState, 'set_buzzer'), pub(LedState, 'set_led')
        self.rgb_pub, self.oled_pub = pub(RGBStates, 'set_rgb'), pub(OLEDState, 'set_oled')
        self.motor_pub = pub(MotorsState, 'set_motor')
        self.pwm_pub = pub(SetPWMServoState, 'pwm_servo/set_state')
        if SetAckerServoState is not None:
            self.acker_pub = self.create_publisher(SetAckerServoState, self.topic('acker_servo/set_state'), 10)
        self.pwm_get = self.create_client(GetPWMServoState, self.topic('pwm_servo/get_state'))
        self.bus_get = self.create_client(GetBusServoState, self.topic('bus_servo/get_state'))

    # ------------------------------------------------------------------ data in
    def add(self, name, store, item):
        if name in self.collect:
            with self.lock:
                store.append((time.time(), *item))

    def on_imu(self, msg):
        if 'imu' not in self.collect:
            return
        o = msg.orientation
        zero = o.x == o.y == o.z == o.w == 0.
        a, g = msg.linear_acceleration, msg.angular_velocity
        with self.lock:
            self.imu.append((time.time(), a.x, a.y, a.z, g.x, g.y, g.z, zero))

    def on_battery(self, msg):
        if 'battery' in self.collect:
            with self.lock:
                self.battery.append((time.time(), msg.data/1000.))

    def listen(self, name, seconds):
        self.collect.add(name)
        time.sleep(seconds)
        self.collect.discard(name)

    # ------------------------------------------------------------------ helpers
    def say(self, text):
        self.get_logger().info(text)

    def record(self, name, status, detail=None, note=''):
        self.results[name] = dict(estado=status, detalle=detail or {}, nota=note)
        self.say(f'[{status}] {name} {note}')

    def stop_motors(self):
        if ButtonState is None:
            return
        zero = MotorsState()
        for i in (1, 2, 3, 4):
            m = MotorState()
            m.id, m.rps = i, 0.
            zero.data.append(m)
        for _ in range(3):
            self.motor_pub.publish(zero)
            time.sleep(0.02)

    # ------------------------------------------------------------------ tests
    def test_topics(self):
        names = dict(self.get_topic_names_and_types())
        pubs = {t: self.count_publishers(t) for t in [self.topic(x) for x in ('imu_raw', 'battery')]}
        subs = {t: self.count_subscribers(t) for t in [self.topic(x) for x in (
            'set_buzzer', 'set_led', 'set_rgb', 'set_oled', 'set_motor', 'pwm_servo/set_state',
            'enable_reception')]}
        status, detail = topic_report(pubs, subs, list(pubs), list(subs))
        extra = {t: self.count_subscribers(self.topic(t)) for t in ('acker_servo/set_state', 'bus_servo/set_state')}
        detail['solo_del_fork_o_opcionales'] = extra
        detail['topics_de_la_placa'] = sorted(n for n in names if n.startswith(self.ns))
        self.record('topics', status, detail, 'la placa debe publicar imu_raw y battery y recibir los set_*')

    def test_enable(self):
        for _ in range(3):
            self.enable_pub.publish(Bool(data=True))
            time.sleep(0.1)
        self.record('enable', 'INFO', note='enable_reception=True enviado: sin esto el nodo oficial no publica')

    def test_battery(self):
        self.say(f'bateria: {self.p["battery_seconds"]:.0f} s (la placa la manda a ~0.5 Hz)')
        self.listen('battery', float(self.p['battery_seconds']))
        self.record('battery', *battery_report([(t, v) for t, v in self.battery]))

    def test_imu(self):
        self.say(f'IMU: {self.p["imu_seconds"]:.0f} s con el coche QUIETO')
        self.listen('imu', float(self.p['imu_seconds']))
        self.record('imu', *imu_report(self.imu))

    def test_button(self):
        self.say(f'BOTON: pulsa la tecla de la placa 1 vez, luego doble click y una pulsacion larga '
                 f'({self.p["button_timeout"]:.0f} s)')
        self.collect.add('button')
        end = time.time()+float(self.p['button_timeout'])
        while time.time() < end:
            time.sleep(0.1)
        self.collect.discard('button')
        status, detail = button_report([(t, i, s) for t, i, s in self.buttons])
        self.record('button', status, detail,
                    'oficial: solo state 1 (pulsar) llega bien; 0=click da error en el nodo; 5/6/7/2 son del fork o no salen')

    def test_buzzer(self):
        for freq in (440, 880, 1760):
            b = BuzzerState()
            b.freq, b.on_time, b.off_time, b.repeat = freq, 0.15, 0.1, 1
            self.buzzer_pub.publish(b)
            time.sleep(0.35)
        self.record('buzzer', 'MANUAL', note='deben sonar 3 tonos, grave -> agudo')

    def test_led(self):
        for led_id in [int(i) for i in self.p['led_ids']]:
            led = LedState()
            led.id, led.on_time, led.off_time, led.repeat = led_id, 0.2, 0.2, 3
            self.led_pub.publish(led)
            time.sleep(1.4)
        self.record('led', 'MANUAL', dict(ids=[int(i) for i in self.p['led_ids']]),
                    'cada LED de la placa (hay 3) debe parpadear 3 veces, uno tras otro')

    def test_rgb(self):
        for rgb in ((RGB_LEVEL, 0, 0), (0, RGB_LEVEL, 0), (0, 0, RGB_LEVEL), (0, 0, 0)):
            states = RGBStates()
            for index in (1, 2):
                s = RGBState()
                s.index, s.red, s.green, s.blue = index, *rgb
                states.states.append(s)
            self.rgb_pub.publish(states)
            time.sleep(0.6)
        self.record('rgb', 'MANUAL', note='los 2 RGB de la placa: rojo, verde, azul, apagado (nivel bajo)')

    def test_oled(self):
        for line, text in enumerate(('RRC test', 'OLED linea 2'), start=1):
            msg = OLEDState()
            msg.index, msg.text = line, text
            self.oled_pub.publish(msg)
            time.sleep(0.3)
        time.sleep(1.5)
        self.record('oled', 'MANUAL', note='la ficha de la RRC Lite no lista pantalla OLED: sin modulo conectado no se vera nada')

    def test_joy(self):
        self.say(f'JOY: mueve el mando conectado a la placa ({self.p["listen_seconds"]:.0f} s)')
        self.listen('joy', float(self.p['listen_seconds']))
        self.record('joy', 'INFO', dict(mensajes=len(self.joy), hz=rate_hz([x[0] for x in self.joy])),
                    'sin mando conectado no llega nada: es normal')

    def test_sbus(self):
        self.say(f'SBUS: enciende la radio ({self.p["listen_seconds"]:.0f} s)')
        self.listen('sbus', float(self.p['listen_seconds']))
        self.record('sbus', 'INFO', dict(mensajes=len(self.sbus), hz=rate_hz([x[0] for x in self.sbus])),
                    'sin receptor SBUS no llega nada: es normal')

    def test_acker_servo(self):
        if SetAckerServoState is None:
            return self.record('acker_servo', 'SKIP', note='SetAckerServoState no existe (no es el fork del equipo)')
        cal = ServoCalibration()
        for deg in (0., SERVO_TEST_DEG, 0., -SERVO_TEST_DEG, 0.):
            msg = SetAckerServoState()
            msg.position = int(round(servo_us(math.radians(deg), cal)))
            msg.duration = 0.3
            self.acker_pub.publish(msg)
            time.sleep(0.8)
        self.record('acker_servo', 'MANUAL', note=f'ruedas: centro, +{SERVO_TEST_DEG:.0f}, centro, -{SERVO_TEST_DEG:.0f}, centro')

    def test_pwm_servo(self):
        if not self.pwm_ids:
            return self.record('pwm_servo', 'SKIP', note='pasa pwm_ids:="[1]" con el servo que quieras mover')
        for position in (1500, 1500+int(self.p['pwm_delta']), 1500, 1500-int(self.p['pwm_delta']), 1500):
            msg = SetPWMServoState()
            msg.duration = 0.3
            for sid in self.pwm_ids:
                state = PWMServoState()
                state.id, state.position = [sid], [position]
                msg.state.append(state)
            self.pwm_pub.publish(msg)
            time.sleep(0.7)
        self.record('pwm_servo', 'MANUAL', dict(ids=self.pwm_ids), note='servos PWM: centro, +, centro, -, centro')

    def call(self, client, request):
        if not client.wait_for_service(timeout_sec=float(self.p['service_timeout'])):
            return None
        future = client.call_async(request)
        end = time.time()+float(self.p['service_timeout'])
        while not future.done() and time.time() < end:
            time.sleep(0.02)
        return future.result() if future.done() else None

    def test_pwm_read(self):
        if not self.pwm_ids:
            return self.record('pwm_read', 'SKIP', note='pasa pwm_ids:="[1,2]"')
        request = GetPWMServoState.Request()
        for sid in self.pwm_ids:
            cmd = GetPWMServoCmd()
            cmd.id, cmd.get_position, cmd.get_offset = sid, 1, 1
            request.cmd.append(cmd)
        response = self.call(self.pwm_get, request)
        if response is None:
            return self.record('pwm_read', 'FAIL', note='sin respuesta (el nodo oficial puede quedar bloqueado: reinicialo)')
        states = [dict(position=list(s.position), offset=list(s.offset)) for s in response.state]
        self.record('pwm_read', 'INFO', dict(ids=self.pwm_ids, estados=states))

    def test_bus_read(self):
        if not self.bus_ids:
            return self.record('bus_read', 'SKIP', note='pasa bus_ids:="[1]" si hay servos de bus')
        request = GetBusServoState.Request()
        for sid in self.bus_ids:
            cmd = GetBusServoCmd()
            cmd.id = sid
            cmd.get_position = cmd.get_voltage = cmd.get_temperature = 1
            request.cmd.append(cmd)
        response = self.call(self.bus_get, request)
        if response is None:
            return self.record('bus_read', 'FAIL', note='sin respuesta (sin servos de bus el nodo oficial se bloquea: reinicialo)')
        states = [dict(position=list(s.position), voltage=list(s.voltage), temperature=list(s.temperature))
                  for s in response.state]
        self.record('bus_read', 'INFO', dict(ids=self.bus_ids, estados=states))

    def test_board_motor(self):
        detail = dict(ids=self.motor_ids, rps=self.motor_rps, segundos=self.motor_time)
        try:
            for motor in self.motor_ids:
                self.say(f'motor {motor} de la placa a {self.motor_rps} rps, {self.motor_time} s')
                end = time.time()+self.motor_time
                while time.time() < end:
                    msg = MotorsState()
                    state = MotorState()
                    state.id, state.rps = motor, float(self.motor_rps)
                    msg.data.append(state)
                    self.motor_pub.publish(msg)
                    time.sleep(0.02)
                self.stop_motors()
                time.sleep(0.8)
        finally:
            self.stop_motors()
        self.record('board_motor', 'MANUAL', detail, note='que gire cada puerto; el motor del coche es el TB6612 del Pi')

    # ------------------------------------------------------------------ run
    def selected(self):
        names = [str(n) for n in self.p['tests']]
        out = []
        for name in names:
            out += SAFE if name == 'safe' else (SAFE+MOVING if name == 'all' else [name])
        out = list(dict.fromkeys(out))
        if 'all' in names and not self.p['wheels_in_air']:
            self.say('"all" incluye pruebas que mueven cosas: solo con wheels_in_air:=true; se omiten.')
            out = [n for n in out if n not in MOVING]
        return out

    def run_all(self):
        if ButtonState is None:
            self.get_logger().error('rrc_lite_msgs no esta instalado: esto se corre en el coche.')
            return
        time.sleep(1.0)    # discovery
        for name in self.selected():
            test = getattr(self, f'test_{name}', None)
            if test is None:
                self.record(name, 'FAIL', note='prueba desconocida')
                continue
            if name in MOVING and name != 'pwm_read' and name != 'bus_read' and not self.p['wheels_in_air']:
                self.record(name, 'SKIP', note='mueve algo: con wheels_in_air:=true (coche levantado)')
                continue
            try:
                test()
            except Exception as error:   # keep going with the rest of the board
                self.record(name, 'FAIL', note=f'error: {error}')
            finally:
                self.stop_motors()
        self.report()

    def report(self):
        with open(os.path.join(self.dir, 'results.json'), 'w') as f:
            json.dump(self.results, f, indent=1, default=str, ensure_ascii=False)
        lines = [f'{v["estado"]:6} {k:12} {v["nota"]}' for k, v in self.results.items()]
        manual = [k for k, v in self.results.items() if v['estado'] == 'MANUAL']
        if manual:
            lines.append('')
            lines.append('Anota a mano (vi/oi): ' + ', '.join(manual))
        with open(os.path.join(self.dir, 'summary.txt'), 'w') as f:
            f.write('\n'.join(lines)+'\n')
        self.say('\n'+'\n'.join(lines)+f'\nResultados en {self.dir}')


def main(args=None):
    rclpy.init(args=args)
    node = RrcTest()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    try:
        node.run_all()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.stop_motors()
        except Exception:
            pass
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()
