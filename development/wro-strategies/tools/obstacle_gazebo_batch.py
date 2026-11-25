#!/usr/bin/env python3
"""Headless Gazebo Obstacle rounds, several at once, each in its own ROS domain and gz partition.

    python3 tools/obstacle_gazebo_batch.py <tag> --jobs 2 --rtf 1                  # standard set, v2
    python3 tools/obstacle_gazebo_batch.py <tag> --fields reg0-cw,reg4-ccw --rtf 3 --repeat 2

Meant for the remote machine (docs/maquina-remota.md). Each round is the normal runner
(run_obstacle_gui_experiment.py: same world, judge, round.json and ledger line); this script only
gives every job its own ROS_DOMAIN_ID and GZ_PARTITION, runs clean_sim.py once before and after the
batch (never between rounds: it would kill the other jobs), and adds the quality gate of the quiet
suites to each line: clean=1 when control ticks are never more than 0.2 s apart and LiDAR stamps stay
within 0.1 s of /clock. `speed` is simulated per wall seconds while the
strategy ran (Gazebo start-up excluded).
"""
import argparse
import csv
import gzip
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT/'src/robotek_evaluation/tools/run_obstacle_gui_experiment.py'
CLEAN = ROOT/'src/robotek_evaluation/tools/clean_sim.py'


def quality(directory):
    """(clean, speed): clean=1 when the strategy kept up with the simulation (same test as
    tools/obstacle_suite_quiet.py); speed is simulated over wall seconds while the strategy ran."""
    try:
        rows = list(csv.DictReader(open(directory/'telemetry.csv')))
        t = [float(r['sim_time']) for r in rows]
        speed = (t[-1]-t[0])/max(float(rows[-1]['wall_time'])-float(rows[0]['wall_time']), 1e-9)
        gaps = [b-a for a, b in zip(t, t[1:]) if 0 < b-a < 1]
        with gzip.open(directory/'scans.jsonl.gz', 'rt') as f:
            scans = [json.loads(line) for line in f][10:]
        lag = [s['stamp']-s['sim_time'] for s in scans]
        return int(bool(gaps) and max(gaps) <= .2 and max(lag) < .1 and min(lag) > -.1), speed
    except (OSError, KeyError, ValueError, IndexError):
        return 0, 0.


def reap(slot):
    """Kill whatever a job left behind: every process with this job's GZ_PARTITION. The runner
    stops the launch with SIGINT, but `gz sim -s` can outlive it, and a server left in the
    partition mixes into the next round (rounds 3-10 of the first capacity test, 26 Oct 2026)."""
    tag, killed = f'GZ_PARTITION=robotek{slot}\0'.encode(), 0
    for environ in Path('/proc').glob('[0-9]*/environ'):
        try:
            if tag in environ.read_bytes():
                os.kill(int(environ.parent.name), 9)
                killed += 1
        except (OSError, ValueError):
            pass
    return killed


def run(job, slot, args):
    name, seed, direction = job
    env = dict(os.environ, ROS_DOMAIN_ID=str(40+slot), GZ_PARTITION=f'robotek{slot}')
    if args.gpu:   # WSL2: Mesa renders through the Windows GPU (d3d12) instead of llvmpipe on the CPU
        env.update(GALLIUM_DRIVER='d3d12', MESA_D3D12_DEFAULT_ADAPTER_NAME=args.gpu)
    command = [sys.executable, str(RUNNER), '--name', name, '--seed', str(seed), '--direction', direction,
               '--strategy', args.strategy, '--steer-p-gain', '20', '--no-gui', '--no-rviz',
               '--real-time-factor', str(args.rtf), '--wall-timeout', str(args.wall_timeout)]+args.runner_arg
    reap(slot)
    out = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True)
    leftover = reap(slot)
    lines = out.stdout.strip().splitlines()
    directory = Path(lines[0]) if lines and lines[0].startswith('/') else None
    if directory is None or not (directory/'round.json').exists():
        lines = (out.stderr or out.stdout or 'no output').strip().splitlines()
        return dict(name=name, error=lines[-1][:200])   # the last line (the exception) is enough
    r = json.load(open(directory/'round.json'))
    v, g = r.get('validation') or {}, r.get('rule_judge') or {}
    clean, speed = quality(directory)
    return dict(name=name, dir=directory.name, points=r.get('points_estimated'), valid=v.get('passed'),
                time=g.get('time_from_start_sim_seconds'), margin=v.get('margin_class'),
                failed=','.join(v.get('failed', [])), clean=clean, speed=speed, leftover=leftover)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('tag')
    parser.add_argument('--fields', help='comma list like reg0-cw,reg4-ccw (default: layouts 0-4, both directions)')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--rtf', type=float, default=1.0, help='real_time_factor (0 = as fast as possible)')
    parser.add_argument('--strategy', default='v3', choices=['v3', 'v2', 'current'])
    parser.add_argument('--gpu', nargs='?', const='NVIDIA', help='WSL2: render with the d3d12 adapter of this name')
    parser.add_argument('--wall-timeout', type=float, default=400.)
    parser.add_argument('--runner-arg', action='append', default=[], help='extra runner argument, e.g. --param=x=1')
    parser.add_argument('--out', type=Path, help='JSON lines with one result per round')
    args = parser.parse_args()
    fields = args.fields.split(',') if args.fields else [f'reg{n}-{d}' for n in range(5) for d in ('ccw', 'cw')]
    jobs = [(f'{args.tag}-{f}' + (f'-r{k}' if args.repeat > 1 else ''), int(f[3:].split('-')[0]), f.split('-')[1])
            for k, f in itertools.product(range(args.repeat), fields)]
    subprocess.run([sys.executable, str(CLEAN)], capture_output=True)
    slots = list(range(args.jobs))
    started = time.time()

    def worker(job):
        slot = slots.pop()
        try:
            return run(job, slot, args)
        finally:
            slots.append(slot)

    results = []
    with ThreadPoolExecutor(args.jobs) as pool:
        for r in pool.map(worker, jobs):
            results.append(r)
            if 'error' in r:
                print(f"{r['name']:<40} ERROR {r['error']}", flush=True)
                continue
            t = '%.1f' % r['time'] if r['time'] else '-'
            print(f"{r['name']:<40} pts={r['points']!s:<3} t={t:<6} valid={r['valid']!s:<5} {r['margin']!s:<9} "
                  f"clean={r['clean']} speed={r['speed']:.2f} left={r['leftover']} {r['failed']}", flush=True)
            if args.out:
                with args.out.open('a') as f:
                    f.write(json.dumps(r)+'\n')
    subprocess.run([sys.executable, str(CLEAN)], capture_output=True)
    ok = [r for r in results if 'error' not in r]
    print(f"valid {sum(bool(r['valid']) for r in ok)}/{len(results)}  clean {sum(r['clean'] for r in ok)}/{len(ok)}  "
          f"jobs {args.jobs} rtf {args.rtf:g}  wall {time.time()-started:.0f} s")


if __name__ == '__main__':
    main()
