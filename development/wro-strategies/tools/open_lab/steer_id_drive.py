"""Publish a scripted steering profile on /cmd_vel_raw at 50 Hz (sim clock) and log every command."""
import math, sys, csv
import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from geometry_msgs.msg import Twist
L = 0.1174
PROFILE = [(2.0, 0.0), (1.6, 0.30), (1.6, 0.10), (1.6, 0.30), (1.6, -0.30), (1.6, 0.0), (1.6, 0.20),
           (1.6, -0.10), (1.6, 0.05), (1.6, 0.0), (1.6, 0.30), (0.5, 0.0), (1.0, -0.30), (0.4, 0.30), (1.2, 0.0),
           (0.6, 0.30), (0.6, -0.30), (0.6, 0.30), (0.6, -0.30), (1.5, 0.0)]
class Drive(Node):
    def __init__(self):
        super().__init__('steer_id_drive', parameter_overrides=[rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.pub = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.t0 = None; self.now = None
        self.create_subscription(Clock, '/clock', self.on_clock, 10)
        self.create_timer(0.02, self.tick)
        self.log = open('/tmp/v5/id/cmd.csv', 'w'); self.log.write('sim_time,v,wz,steer\n')
        self.edges = []; t = 0.0
        for d, s in PROFILE: self.edges.append((t, t + d, s)); t += d
        self.end = t
    def on_clock(self, m): self.now = m.clock.sec + m.clock.nanosec * 1e-9
    def tick(self):
        if self.now is None: return
        if self.t0 is None: self.t0 = self.now + 8.0   # let the plugin and sensors settle
        t = self.now - self.t0
        if t > self.end + 1.0:
            self.log.close(); self.get_logger().info('done'); raise SystemExit
        steer = 0.0
        for a, b, s in self.edges:
            if a <= t < b: steer = s
        v = 1.28 if t >= 0 else 0.0
        msg = Twist(); msg.linear.x = v; msg.angular.z = v * math.tan(steer) / L if v else 0.0
        self.pub.publish(msg)
        self.log.write('%.4f,%.3f,%.4f,%.4f\n' % (self.now, v, msg.angular.z, steer))
rclpy.init(); n = Drive()
try: rclpy.spin(n)
except SystemExit: pass
