"""Camera and lidar perception for the Obstacle round.

- Signs: short isolated lidar clusters (scan_clusters) paired with red/green
  camera blobs by bearing (color_blocks + associate).
- Direction: the orange/blue field lines seen by the camera (LineDirection),
  only a fallback when the wall fit cannot tell CW from CCW.
"""
import math

import cv2
import numpy as np

from .obstacle_field import CAMERA_HFOV, CAMERA_OFFSET_X, CAMERA_PITCH, LIDAR_OFFSET_X, wrap


def scan_clusters(scan):
    """Extract short isolated scan components; wall segments are excluded."""
    groups, group = [], []
    for i, distance in enumerate(scan.ranges):
        if not math.isfinite(distance) or not scan.range_min < distance < 2.5:
            if group:
                groups.append(group)
            group = []
            continue
        angle = scan.angle_min + i * scan.angle_increment
        point = (distance * math.cos(angle), distance * math.sin(angle))
        if group and math.dist(point, group[-1]) > .07:
            groups.append(group)
            group = []
        group.append(point)
    if group:
        groups.append(group)
    result = []
    for points in groups:
        if len(points) < 2:
            continue
        pts = np.array(points)
        diameter = math.hypot(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
        if not .015 <= diameter <= .12:
            continue
        x, y = pts.mean(axis=0)
        distance = math.hypot(x, y)
        # Correct the observed front surface toward the 5 cm pillar center.
        x += .025 * x / distance
        y += .025 * y / distance
        result.append(dict(x=float(x + LIDAR_OFFSET_X), y=float(y), points=len(points),
                           diameter_m=diameter))
    return result


# HSV (low, high) ranges per sign colour, tuned on the simulated camera.
SIM_COLOR_RANGES = {
    'red': [((0, 90, 45), (8, 255, 255)), ((170, 90, 45), (179, 255, 255))],
    'green': [((35, 70, 45), (85, 255, 255))],
}


def color_blocks(bgr, ranges=SIM_COLOR_RANGES, min_area=30, hfov=CAMERA_HFOV, pitch=CAMERA_PITCH, yaw=0.):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    masks = {}
    for color, bands in ranges.items():
        mask = cv2.inRange(hsv, np.array(bands[0][0]), np.array(bands[0][1]))
        for low, high in bands[1:]:
            mask |= cv2.inRange(hsv, np.array(low), np.array(high))
        masks[color] = mask
    blocks = []
    height, width = bgr.shape[:2]
    focal = width / (2 * math.tan(hfov / 2))
    for color, mask in masks.items():
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if cv2.contourArea(contour) < min_area or h < 8 or h < 1.05 * w:
                continue
            u = (x + w / 2 - width / 2) / focal
            v = (y + h / 2 - height / 2) / focal
            bearing = math.atan2(-u, math.cos(pitch) - v * math.sin(pitch)) + yaw
            blocks.append(dict(color=color, bearing=bearing, box=(x, y, w, h)))
    return blocks


def associate(blocks, clusters, angular_gate=.12):
    """Associate each colored ray to a unique scan cluster; reject conflicts."""
    proposals = {}
    for block in blocks:
        matches = [(abs(wrap(math.atan2(c['y'], c['x'] - CAMERA_OFFSET_X) - block['bearing'])), i)
                   for i, c in enumerate(clusters)]
        matches = [pair for pair in matches if pair[0] < angular_gate]
        if not matches:
            continue
        error, index = min(matches)
        proposals.setdefault(index, []).append((block, error))
    result = []
    for index, matches in proposals.items():
        if len({b['color'] for b, _ in matches}) != 1:
            continue
        block, error = min(matches, key=lambda pair: pair[1])
        result.append(dict(clusters[index], color=block['color'],
                           angular_error=error, box=block['box']))
    return result


class LineDirection:
    """Debounce geometrical line evidence from independent camera frames."""

    def __init__(self, min_length=40.0, min_confidence=0.25, confirmations=5):
        self.min_length = min_length
        self.min_confidence = min_confidence
        self.confirmations = confirmations
        self.blue_length = 0.0
        self.orange_length = 0.0
        self.confidence = 0.0
        self.candidate = 0
        self.direction = 0
        self.hits = 0
        self.stamp = None
        self.overlay = None

    @staticmethod
    def line_length(mask):
        """Measure the longest elongated colour component, in image pixels."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        lengths = []
        for contour in contours:
            if cv2.contourArea(contour) < 25:
                continue
            _, dimensions, _ = cv2.minAreaRect(contour)
            short, long = sorted(dimensions)
            if long >= 3 * max(short, 1.0):
                lengths.append(long)
        return max(lengths, default=0.0)

    def update(self, bgr, stamp):
        """Use each frame once; absent or balanced lines cannot choose a turn."""
        if self.stamp is not None and stamp <= self.stamp:
            return
        self.stamp = stamp
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        blue = cv2.inRange(hsv, np.array([90, 60, 60]), np.array([135, 255, 255]))
        orange = cv2.inRange(hsv, np.array([5, 60, 60]), np.array([28, 255, 255]))
        kernel = np.ones((3, 5), dtype=np.uint8)
        blue = cv2.morphologyEx(blue, cv2.MORPH_CLOSE, kernel)
        orange = cv2.morphologyEx(orange, cv2.MORPH_CLOSE, kernel)
        # The downward camera sees the distant lines near the image's top.
        # Only remove the top strip; a lower-half ROI loses both lines.
        top = int(bgr.shape[0] * 0.08)
        blue[:top] = 0
        orange[:top] = 0
        self.blue_length = self.line_length(blue)
        self.orange_length = self.line_length(orange)
        longest = max(self.blue_length, self.orange_length)
        self.confidence = abs(self.blue_length - self.orange_length) / max(longest, 1.0)
        candidate = 0
        if longest >= self.min_length and self.confidence >= self.min_confidence:
            candidate = 1 if self.blue_length > self.orange_length else -1
        self.hits = self.hits + 1 if candidate and candidate == self.candidate else 0
        if candidate and candidate != self.candidate:
            self.hits = 1
        self.candidate = candidate
        self.direction = candidate if self.hits >= self.confirmations else 0
        self.overlay = bgr.copy()
        self.overlay[blue != 0] = (255, 0, 0)
        self.overlay[orange != 0] = (0, 128, 255)
        cv2.line(self.overlay, (0, top), (bgr.shape[1] - 1, top), (0, 255, 0), 1)
        cv2.putText(self.overlay,
                    f'B={self.blue_length:.0f} O={self.orange_length:.0f} '
                    f'conf={self.confidence:.2f} dir={self.direction:+d}',
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
