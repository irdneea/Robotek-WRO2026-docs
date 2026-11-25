"""Write Obstacle evidence (telemetry, scans, detections, camera, planner, replay trace).

No ROS and no control logic. Ground-truth and steering-joint columns are left
empty: the audit recorders fill them after the round.
"""
import csv
import gzip
import json
import math
from pathlib import Path
import time

import cv2

TELEMETRY_COLUMNS = (
    'wall_time', 'sim_time', 'state', 'selected_direction',
    'x_track', 'y_track', 'th_track', 'progress',  # own pose (mirrored track frame) and progress
    'yaw_relative', 'gyro', 'v_cmd', 'w_cmd', 'scan_age', 'image_age',
    'travelled', 'lidar_odom_quality',
    'x_gt', 'y_gt', 'yaw_gt', 'steer_actual', 'steer_right_actual',  # audit only
)
TELEMETRY_PERIOD = .09  # s of simulated time
PLANNER_PERIOD = .2
IMAGE_PERIOD = .5


class ObstacleRecording:
    def __init__(self, telemetry_path):
        path = Path(telemetry_path)
        self.directory = path.parent
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory/'camera').mkdir(exist_ok=True)
        self._csv_file = path.open('w', newline='')
        self._telemetry = csv.DictWriter(self._csv_file, fieldnames=TELEMETRY_COLUMNS)
        self._telemetry.writeheader()
        self._events = (self.directory/'events.jsonl').open('w')
        self._scans = gzip.open(self.directory/'scans.jsonl.gz', 'wt')
        self._detections = (self.directory/'detections.jsonl').open('w')
        self._planner = (self.directory/'planner.jsonl').open('w')
        # Ordered input/output trace for offline replay (scan ranges in scans.jsonl.gz).
        self._trace = gzip.open(self.directory/'trace.jsonl.gz', 'wt')
        self._last = dict(telemetry=-math.inf, planner=-math.inf, image=-math.inf)

    def _due(self, key, now, period):
        if now-self._last[key] < period:
            return False
        self._last[key] = now
        return True

    def event(self, name, sim_time):
        self._events.write(json.dumps(dict(event=name, sim_time=sim_time, wall_time=time.time()))+'\n')
        self._events.flush()

    def record(self, **fields):
        """Free-form event (e.g. a parking plan) in events.jsonl."""
        self._events.write(json.dumps(dict(wall_time=time.time(), **fields))+'\n')
        self._events.flush()

    def scan(self, msg, stamp, sim_time):
        self._scans.write(json.dumps(dict(
            stamp=stamp, sim_time=sim_time, angle_min=msg.angle_min,
            angle_increment=msg.angle_increment, range_min=msg.range_min, range_max=msg.range_max,
            ranges=[v if math.isfinite(v) else None for v in msg.ranges]))+'\n')

    def trace(self, **record):
        self._trace.write(json.dumps(record)+'\n')

    def detections(self, stamp, sim_time, scan_stamp, blocks, clusters, associated):
        self._detections.write(json.dumps(dict(
            stamp=stamp, sim_time=sim_time, scan_stamp=scan_stamp, blocks=blocks,
            clusters=clusters, associated=associated))+'\n')

    def camera(self, bgr, sim_time):
        if self._due('image', sim_time, IMAGE_PERIOD):
            cv2.imwrite(str(self.directory/'camera'/f'{sim_time:09.3f}.jpg'), bgr)

    def control(self, sim_time, **sample):
        if self._due('telemetry', sim_time, TELEMETRY_PERIOD):
            self._telemetry.writerow(dict(dict.fromkeys(TELEMETRY_COLUMNS, math.nan),
                                          wall_time=time.time(), sim_time=sim_time, **sample))
            self._csv_file.flush()

    def planner(self, sim_time, snapshot):
        if self._due('planner', sim_time, PLANNER_PERIOD):
            self._planner.write(json.dumps(dict(sim_time=sim_time, **snapshot))+'\n')

    def close(self):
        for stream in (self._csv_file, self._events, self._scans, self._detections,
                       self._planner, self._trace):
            stream.close()
