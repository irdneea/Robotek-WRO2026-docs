"""Replay a real-car Obstacle v3 bag through robotek-learn's Strategy (scan, IMU, paired signs, Start), ticking at
the recorded /cmd_vel_raw times, and compare the steering with the car's."""
import sys, math
L = '/home/user/Projects/robotek-learn/src/'
sys.path[:0] = [L + 'robotek_obstacle_v3', L + 'robotek_course', L + 'robotek_common']
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from robotek_obstacle_v3.strategy import Strategy
from robotek_common.vehicle import WHEELBASE
import robotek_obstacle_v3.mission as M

bag, t_end = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
r = rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=bag, storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
types = {t.name: t.type for t in r.get_all_topics_and_types()}
r.set_filter(rosbag2_py.StorageFilter(topics=['/robotek/scan', '/robotek/imu', '/obstacle/signs', '/cmd_vel_raw', '/start']))
st = Strategy('auto'); st.auto_start = False
stamp = lambda m: m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
t0 = None; last_t = None; last_sign_stamp = None; rows = []
log = {}
orig = M.Mission._steer
def steer_spy(self, x, y, th, gyro):
    px, py, heading, _ = self._reference(self.phi)
    preview = max(M.PREVIEW, abs(self.speed) * self.p.preview_time)
    kappa = self._reference(M.scene.advance(self.phi, preview))[3]
    error = -(x - px) * math.sin(heading) + (y - py) * math.cos(heading)
    log.update(px=px, py=py, heading=heading, kappa=kappa, error=error, ff=math.atan(WHEELBASE * kappa),
               offset=self._offset_at(self.phi))
    return orig(self, x, y, th, gyro)
M.Mission._steer = steer_spy
while r.has_next():
    tp, d, t = r.read_next(); t *= 1e-9
    m = deserialize_message(d, get_message(types[tp]))
    if tp == '/start' and m.data:
        st.request_start(); t0 = t
    elif tp == '/robotek/scan':
        st.on_scan(m)
    elif tp == '/robotek/imu':
        st.on_imu(stamp(m), m.angular_velocity.z)
    elif tp == '/obstacle/signs':
        obs = [dict(x=k.pose.position.x, y=k.pose.position.y, color='red' if k.color.r > 0.5 else 'green')
               for k in m.markers if k.ns == 'signs']
        st.on_signs(obs, stamp(m.markers[-1]) if m.markers and m.markers[-1].header.stamp.sec else t)
    elif tp == '/cmd_vel_raw':
        dt = 0.02 if last_t is None else t - last_t
        last_t = t
        log.clear()
        v, s = st.control(t, 1 / 50.0)
        if t0 is not None and t - t0 <= t_end:
            car = math.degrees(math.atan(m.angular.z * WHEELBASE / m.linear.x)) if m.linear.x else 0.0
            mi = st.mission
            rows.append((t - t0, v, math.degrees(s), m.linear.x, car, st.label, mi.pose, mi.phi, dict(log),
                         getattr(mi, 'pillar', None)))
step = 0
for tt, v, s, cv, cs, lab, pose, phi, lg, pil in rows:
    if tt >= step:
        x, y, th = pose
        extra = ' '.join('%s %.3f' % (k, math.degrees(val) if k in ('heading', 'ff') else val) for k, val in lg.items())
        print('t %5.2f %-11s replay v %.2f st %+6.1f | car v %.2f st %+6.1f | x %.2f y %.2f th %+6.1f phi %.2f | %s | pillar %s'
              % (tt, lab, v, s, cv, cs, x, y, math.degrees(th), phi, extra, pil))
        step += 0.1
