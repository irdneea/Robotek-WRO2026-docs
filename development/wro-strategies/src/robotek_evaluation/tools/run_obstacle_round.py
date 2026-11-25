#!/usr/bin/env python3
"""Run one recorded Obstacle round (run_obstacle_gui_experiment.py) on a clean machine. Arguments go to the runner."""
import sys

from recorded_run import run

if __name__ == '__main__':
    sys.exit(run('run_obstacle_gui_experiment.py', sys.argv[1:]))
