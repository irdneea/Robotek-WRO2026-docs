import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
d = sys.argv[1]
r = rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=d, storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
types = {t.name: t.type for t in r.get_all_topics_and_types()}
want = {'/obstacle/pose', '/cmd_vel_raw', '/robotek/state', '/rrc/set_motor', '/robotek/scan', '/rrc/acker_servo/set_state'}
r.set_filter(rosbag2_py.StorageFilter(topics=list(want)))
t0 = None; last = {}; rows = []
while r.has_next():
    topic, data, t = r.read_next(); t *= 1e-9
    m = deserialize_message(data, get_message(types[topic]))
    if topic == '/robotek/state': print('%.2f state %s' % (t - (t0 or t), m.data)); continue
    if topic == '/cmd_vel_raw':
        if t0 is None and m.linear.x > 0: t0 = t
        last['cmd'] = (m.linear.x, m.angular.z)
    elif topic == '/obstacle/pose': last['pose'] = list(m.data)
    elif topic == '/robotek/scan':
        rs = m.ranges; n = len(rs)
        def at(deg):
            i = int(round((math.radians(deg) - m.angle_min) / m.angle_increment)) % n
            v = [x for x in rs[max(0,i-3):i+4] if math.isfinite(x) and x > 0.02]
            return min(v) if v else float('nan')
        last['scan'] = (at(0), at(90), at(-90))
        if t0 is not None and 'pose' in last and 'cmd' in last:
            rows.append((t - t0, last['cmd'], last['pose'], last['scan']))
step = 0
for row in rows:
    if row[0] >= step:
        tt, (v, w), (x, y, th, ph), (f, l, rr) = row
        steer = math.degrees(math.atan(w * 0.11883 / v)) if v else 0
        print('t %5.1f v %.2f steer %5.1f | pose x %.2f y %.2f th %6.1f prog %.2f | front %.2f left %.2f right %.2f' % (tt, v, steer, x, y, math.degrees(th), ph, f, l, rr))
        step += 0.5
