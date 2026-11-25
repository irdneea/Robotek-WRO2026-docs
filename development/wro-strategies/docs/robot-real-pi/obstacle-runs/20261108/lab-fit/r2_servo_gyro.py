"""Servo command vs gyro and LiDAR front/sides, round 2 of 4 nov (first seconds after the first motion)."""
import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
d = sys.argv[1]; t_end = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
r = rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=d, storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
types = {t.name: t.type for t in r.get_all_topics_and_types()}
want = ['/cmd_vel_raw', '/robotek/imu', '/rrc/acker_servo/set_state', '/rrc/set_motor', '/robotek/scan']
r.set_filter(rosbag2_py.StorageFilter(topics=[w for w in want if w in types]))
t0 = None; servo = motor = cmd = None; gz = 0.0; scan = (0, 0, 0)
out = []
while r.has_next():
    topic, data, t = r.read_next(); t *= 1e-9
    m = deserialize_message(data, get_message(types[topic]))
    if topic == '/cmd_vel_raw':
        cmd = (m.linear.x, m.angular.z)
        if t0 is None and m.linear.x > 0: t0 = t
    elif topic == '/robotek/imu': gz = m.angular_velocity.z
    elif topic == '/rrc/acker_servo/set_state':
        try: servo = m.state[0].position[0] if hasattr(m, 'state') else str(m)[:60]
        except Exception: servo = str(m)[:80]
    elif topic == '/rrc/set_motor':
        try: motor = m.data[0].rps
        except Exception: motor = str(m)[:60]
    elif topic == '/robotek/scan':
        rs = m.ranges; n = len(rs)
        def at(deg):
            i = int(round((math.radians(deg) - m.angle_min) / m.angle_increment)) % n
            v = [x for x in rs[max(0, i-3):i+4] if math.isfinite(x) and x > 0.02]
            return min(v) if v else float('nan')
        scan = (at(0), at(90), at(-90))
    if t0 is not None and topic in ('/robotek/imu',):
        if t - t0 > t_end: break
        out.append((t - t0, cmd, servo, motor, gz, scan))
for row in out:
    t, cmd, servo, motor, gz, scan = row
    print('%.3f cmd %s servo %s motor %s gz %+.2f front %.2f L %.2f R %.2f' % (t, cmd and ('%.2f %.2f' % cmd), servo, motor, gz, *scan))
