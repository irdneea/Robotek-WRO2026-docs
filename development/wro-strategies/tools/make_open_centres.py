#!/usr/bin/env python3
"""The 16 Open island layouts of the rules: each side's corridor 1.0 m (wide) or 0.6 m (narrow).

Writes docs/open-challenge-runs/field-size-driver/worlds-centres/c<E><N><W><S>.sdf (W = wide, N = narrow per side,
east, north, west, south) from square100.sdf, moving only the four island walls. open_lab's suite `centres` runs them.
"""
from itertools import product
from pathlib import Path
import re

WORLDS = Path(__file__).resolve().parents[1] / 'docs/open-challenge-runs/field-size-driver/worlds'
OUT = WORLDS.parent / 'worlds-centres'
OUTER, T = 1.5, 0.04          # inner face of the outer walls; wall thickness


def layouts():
    for combo in product('WN', repeat=4):
        yield 'c' + ''.join(combo), dict(zip(('east', 'north', 'west', 'south'), combo))


def island(sides):
    face = {s: OUTER - (1.0 if k == 'W' else 0.6) for s, k in sides.items()}    # island face distance from 0
    xmin, xmax, ymin, ymax = -face['west'], face['east'], -face['south'], face['north']
    walls = {'east': (xmax - T / 2, (ymin + ymax) / 2, T, ymax - ymin),
             'west': (xmin + T / 2, (ymin + ymax) / 2, T, ymax - ymin),
             'north': ((xmin + xmax) / 2, ymax - T / 2, xmax - xmin, T),
             'south': ((xmin + xmax) / 2, ymin + T / 2, xmax - xmin, T)}
    return walls


def main():
    template = (WORLDS / 'square100.sdf').read_text()
    OUT.mkdir(exist_ok=True)
    for name, sides in layouts():
        text = template
        for side, (x, y, sx, sy) in island(sides).items():
            for tag in (f'wall_int_{side}"', f'wall_int_{side}_col"'):
                pattern = re.compile(r'(name="' + re.escape(tag) + r'>\s*<pose>)[^<]*(</pose>.*?<size>)[^<]*(</size>)',
                                     re.S)
                text, n = pattern.subn(lambda m: f'{m.group(1)}{x:.3f} {y:.3f} 0.06 0 0 0{m.group(2)}'
                                                 f'{sx:.3f} {sy:.3f} 0.1{m.group(3)}', text, count=1)
                assert n == 1, (name, tag)
        (OUT / f'{name}.sdf').write_text(text)
    print(f'16 layouts in {OUT}')


if __name__ == '__main__':
    main()
