import sys, math, rosbag2_py, numpy as np
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
bag, out = sys.argv[1], sys.argv[2]
r=rosbag2_py.SequentialReader(); r.open(rosbag2_py.StorageOptions(uri=bag,storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
types={t.name:t.type for t in r.get_all_topics_and_types()}
r.set_filter(rosbag2_py.StorageFilter(topics=['/robotek/scan','/obstacle/pose']))
scan=pose=None; track=[]
while r.has_next():
    tp,d,t=r.read_next(); m=deserialize_message(d,get_message(types[tp]))
    if tp=='/robotek/scan': scan=m
    else:
        pose=list(m.data)
        if all(map(math.isfinite,pose[:3])): track.append(pose[:3])
x,y,th=track[-1]
rs=np.asarray(scan.ranges); a=scan.angle_min+scan.angle_increment*np.arange(len(rs)); ok=np.isfinite(rs)&(rs>0.05)&(rs<3)
np.savez(out, rs=rs, a=a, track=np.array(track))
