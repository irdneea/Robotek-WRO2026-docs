#!/usr/bin/env python3
"""Heavy runs on a remote machine (decision of 26 Oct 2026): headless Gazebo rounds, the labs and the quiet suites.

    tools/remote.py sync              # copy this working tree (uncommitted changes too) and build there
    tools/remote.py run <command...>  # run from the remote repository root, with ROS Jazzy loaded
    tools/remote.py run 'a && b'      # one argument: a shell line
    tools/remote.py fetch             # bring the new rounds back and append their ledger lines here

Typical: tools/remote.py sync && tools/remote.py run python3 tools/obstacle_lab_suite.py --seeds 0-4
         tools/remote.py run tools/obstacle_suite_quiet.py <tag> && tools/remote.py fetch
Set REMOTE (an ssh host) and, if needed, REMOTE_DIR. The remote was WSL2 Ubuntu 24.04 with ROS Jazzy from apt
(docs/maquina-remota.md). `sync` fetches first and then puts these ledgers on the remote, so `fetch` appends exactly
the remote's new lines. Fetch before running rounds here again.
"""
import json
import os
import shlex
import subprocess
import sys

import devenv

REMOTE = os.environ.get('REMOTE') or 'REMOTE_HOST'
REMOTE_DIR = os.environ.get('REMOTE_DIR') or 'Projects/WRO-Strategies'
RUN_DIRS = ['docs/open-challenge-runs', 'docs/obstacle-challenge-runs']
LEDGERS = [f'{d}/rounds.jsonl' for d in RUN_DIRS]


def remote_line(command):
    """The argument given to ssh: a login bash in the remote repository, with ROS and the workspace loaded."""
    script = (f'cd {REMOTE_DIR} && source /opt/ros/jazzy/setup.bash && '
              '{ [ ! -f install/setup.bash ] || source install/setup.bash; } && ' + command)
    return 'bash -lc ' + shlex.quote(script)


def run_command(args):
    """One argument is a shell line ('a && b'); several are a command and its arguments."""
    return args[0] if len(args) == 1 else ' '.join(shlex.quote(a) for a in args)


def call(command):
    sys.stdout.flush()
    subprocess.run(command, check=True)


def remote(command):
    call(['ssh', '-o', 'BatchMode=yes', REMOTE, remote_line(command)])


def tag_lines(text, host):
    """Parse the new ledger lines of the remote and note where they ran."""
    rounds = []
    for line in text.splitlines():
        if line.strip():
            round_ = json.loads(line)
            round_.setdefault('host', host)
            rounds.append(round_)
    return rounds


def fetch():
    for folder in RUN_DIRS:
        call(['rsync', '-a', '--ignore-existing', '--exclude', 'rounds.jsonl', f'{REMOTE}:{REMOTE_DIR}/{folder}/',
              f'{folder}/'])
    for ledger in LEDGERS:
        with open(ledger, 'rb') as f:
            count = f.read().count(b'\n')
        tail = subprocess.run(['ssh', '-o', 'BatchMode=yes', REMOTE, f'tail -n +{count + 1} {REMOTE_DIR}/{ledger}'],
                              stdout=subprocess.PIPE, text=True, encoding='utf-8', check=True).stdout
        rounds = tag_lines(tail, f'{REMOTE} (WSL2 Ubuntu 24.04, ROS Jazzy apt)')
        with open(ledger, 'a', encoding='utf-8') as f:
            for round_ in rounds:
                f.write(json.dumps(round_, ensure_ascii=False) + '\n')
        for round_ in rounds:
            print('fetched', round_.get('name') or round_.get('run'), 'pts', round_.get('points_estimated'))
        call(['rsync', '-a', ledger, f'{REMOTE}:{REMOTE_DIR}/{ledger}'])


def sync():
    # Fetch first: the rsync below puts these ledgers on the remote, which would drop its new lines.
    fetch()
    # Round folders stay where they ran; src and tools mirror this machine exactly.
    call(['rsync', '-a', '--exclude', '.git', '--exclude', '/build', '--exclude', '/install', '--exclude', '/log',
          '--exclude', '__pycache__', '--exclude', '/docs/*-challenge-runs/2*/', '--exclude', '/Robotek-WRO2026',
          '--exclude', '/plans', './', f'{REMOTE}:{REMOTE_DIR}/'])
    call(['rsync', '-a', '--delete', '--exclude', '__pycache__', 'src', 'tools', f'{REMOTE}:{REMOTE_DIR}/'])
    remote('colcon build --symlink-install 2>&1 | tail -2')


def main(argv):
    os.chdir(devenv.ROOT)
    try:
        if argv[:1] == ['sync']:
            sync()
        elif argv[:1] == ['run'] and len(argv) > 1:
            remote(run_command(argv[1:]))
        elif argv[:1] == ['fetch']:
            fetch()
        else:
            print(__doc__)
            return 2
    except subprocess.CalledProcessError as error:
        return error.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
