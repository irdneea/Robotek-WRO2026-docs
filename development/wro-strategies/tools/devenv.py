"""Shared helpers of the scripts of this workspace (not run on its own).

ROS only offers shell files to load its environment, so they are loaded in a shell that then prints it.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ROS_SETUP = os.environ.get('ROBOTEK_ROS_SETUP', '/opt/ros/jazzy/setup.bash')
EVALUATION_TOOLS = ROOT / 'src/robotek_evaluation/tools'


def sourced(files, env=None):
    """The environment after loading, in order, the shell setup files that exist."""
    files = [str(f) for f in files if os.path.isfile(f)]
    load = 'for f in "$@"; do source "$f" >/dev/null || exit 1; done; env -0'
    result = subprocess.run(['bash', '-c', load, 'bash', *files], stdout=subprocess.PIPE, env=env, cwd=ROOT)
    if result.returncode:
        sys.exit('Could not load the ROS environment: ' + ' '.join(files))
    return dict(entry.split('=', 1) for entry in result.stdout.decode().split('\0') if '=' in entry)


def workspace_env():
    """ROS and this workspace. On macOS it is the RoboStack environment of macos_env.py."""
    if sys.platform == 'darwin':
        import macos_env
        return macos_env.environment()
    return sourced([ROS_SETUP, ROOT / 'install/setup.bash'])


def load_average():
    """The one-minute load of the machine, without decimals (Linux and macOS)."""
    return int(os.getloadavg()[0])


def wait_until_quiet(limit):
    """Rounds measured on a busy machine are not valid: wait until the load is at most ``limit``."""
    while load_average() > limit:
        time.sleep(20)


def newest(folder, suffix):
    """The most recently modified round folder of docs/<folder> whose name ends in ``suffix`` (None if none)."""
    found = [p for p in (ROOT / 'docs' / folder).glob('*' + suffix) if p.is_dir()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def read_round(path):
    return json.loads((Path(path) / 'round.json').read_text())


def sim_time(round_):
    value = (round_.get('rule_judge') or {}).get('time_from_start_sim_seconds')
    return '%.2f' % value if value else '-'


def run_tool(path, *args, **kwargs):
    """Run another Python script with this same Python."""
    sys.stdout.flush()
    return subprocess.run([sys.executable, str(path), *[str(a) for a in args]], **kwargs)
