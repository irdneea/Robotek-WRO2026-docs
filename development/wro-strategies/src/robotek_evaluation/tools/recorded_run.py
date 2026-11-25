"""Run a recorded experiment against the built workspace: clean, run the runner, clean again (not run on its own).

Linux uses the system ROS; macOS the RoboStack environment (tools/macos_env.py, docs/simulacion-macos.md).
"""
from pathlib import Path
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
import devenv  # noqa: E402


def run(runner, argv):
    env = devenv.workspace_env()
    clean = HERE / 'clean_sim.py'
    devenv.run_tool(clean, env=env)
    process = None
    # A SIGTERM must also clean up: turn it into an exception so that `finally` runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        sys.stdout.flush()
        process = subprocess.Popen([sys.executable, str(HERE / runner), *argv], env=env, cwd=devenv.ROOT)
        return process.wait()
    except KeyboardInterrupt:
        return process.wait() if process else 130       # Ctrl-C reaches the runner too: let it save the round
    finally:
        devenv.run_tool(clean, env=env)
