"""Map of the 24 regulation sign seats: lidar hits locate a sign, camera votes its colour."""
import math

import numpy as np

from .obstacle_field import make_seats


class SeatMap:
    def __init__(self):
        self.seats = make_seats()
        self.hits = np.zeros(len(self.seats))
        self.votes = [dict(red=0, green=0) for _ in self.seats]

    def _nearest(self, x, y, gate):
        best = min(self.seats, key=lambda s: math.hypot(s['x']-x, s['y']-y))
        return best if math.hypot(best['x']-x, best['y']-y) < gate else None

    def lidar(self, clusters, pose):
        x, y, th = pose
        c, s = math.cos(th), math.sin(th)
        for bx, by in clusters:
            seat = self._nearest(x+c*bx-s*by, y+s*bx+c*by, .10)
            if seat:
                self.hits[seat['id']] = min(self.hits[seat['id']]+1, 50)

    def camera(self, observations, pose):
        x, y, th = pose
        c, s = math.cos(th), math.sin(th)
        for bx, by, color in observations:
            seat = self._nearest(x+c*bx-s*by, y+s*bx+c*by, .14)
            if seat:
                self.votes[seat['id']][color] += 1

    def pillars(self, min_hits=3, min_votes=2):
        """At most one sign per (section, along) slot: the cards never use both rows.

        The two rows are only 0.2 m apart, so localization error spreads lidar hits
        and colour votes over both seats; keep the row with more lidar hits and pool
        the colour votes of the slot.
        """
        result = []
        for k in range(0, len(self.seats), 2):
            pair = self.seats[k:k+2]
            hits = [self.hits[s['id']] for s in pair]
            votes = {c: sum(self.votes[s['id']][c] for s in pair) for c in ('red', 'green')}
            if max(hits) < min_hits and max(votes.values()) < min_votes:
                continue
            seat = pair[0] if hits[0] >= hits[1] else pair[1]
            if max(hits) < min_hits:  # colour seen but few lidar hits: use camera evidence
                cam = [sum(self.votes[s['id']].values()) for s in pair]
                seat = pair[0] if cam[0] >= cam[1] else pair[1]
            color = None
            if max(votes.values()) >= min_votes:
                color = 'red' if votes['red'] > votes['green'] else 'green'
            result.append(dict(seat, color=color))
        return result
