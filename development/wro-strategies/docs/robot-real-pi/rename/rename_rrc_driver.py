#!/usr/bin/env python3
"""Rename the RRC Lite driver on the Pi (decision of 10 Oct 2026, see README.md "Nombres nuevos"):

    package  ros_robot_controller       -> rrc_lite_driver
    messages ros_robot_controller_msgs  -> rrc_lite_msgs
    executable controller_node          -> rrc_driver      (node name rrc_driver)
    topics   /ros_robot_controller/...  -> /rrc/...

Historical record: the migration already ran on the car on 9 Oct 2026 as a shell script; this is its translation.
Two rules of the first version were too broad (package_name= and get_package_share_directory('...') became
rrc_driver) and were fixed by hand on the Pi; they are corrected here.

Run ON THE PI, with the ROS stack stopped:
    ssh <user>@<car-address> python3 - < docs/robot-real-pi/rename/rename_rrc_driver.py
Dry run (only shows what it would touch):
    ssh <user>@<car-address> DRY_RUN=1 python3 - < docs/robot-real-pi/rename/rename_rrc_driver.py

Nothing is deleted: the old sources, scripts and install/build folders are copied or moved to
~/rename-backup-<stamp>/. Rollback instructions are printed at the end.
"""
import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HOME = Path.home()
SKIP_DIRS = {'.git', 'build', 'install', 'log'}
OLD_NAMES = re.compile(r'ros_robot_controller|controller_node')
STOP_PATTERN_OLD = "ros_robot_controller/.*/controller_node"

# The replacements of the original (sed), in the same order: the order matters.
RULES = [
    (r'ros_robot_controller_msgs', 'rrc_lite_msgs'),
    (r'/ros_robot_controller/(battery|button|imu_raw|joy|sbus|set_|enable_reception|pwm_servo|bus_servo|acker_servo'
     r'|init_finish|get_)', r'/rrc/\1'),
    (r'controller_node *= *ros_robot_controller\.controller_node:main', 'rrc_driver = rrc_lite_driver.rrc_driver:main'),
    (r'ros_robot_controller\.controller_node', 'rrc_lite_driver.rrc_driver'),
    (r"executable *= *'controller_node'", "executable='rrc_driver'"),
    (r'executable *= *"controller_node"', 'executable="rrc_driver"'),
    (r'''\bname *= *(['"])ros_robot_controller(['"])''', r'name=\1rrc_driver\2'),
    (r'''RosRobotController\((['"])ros_robot_controller''', r'RosRobotController(\1rrc_driver'),
    (r'ros_robot_controller', 'rrc_lite_driver'),
    (r'controller_node', 'rrc_driver'),
]


def replace_names(text):
    for pattern, replacement in RULES:
        text = re.sub(pattern, replacement, text)
    return text


def private_topics(text):
    """The driver's topics were private ("~/battery" -> /<node name>/battery). Make them rrc/..."""
    return re.sub(r'''(["'])~/''', r'\1rrc/', text)


def text_files(folders):
    """Text files under the folders that still use the old names (backups, logs and build folders left out)."""
    for folder in folders:
        for base, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                path = Path(base) / name
                if '.bak' in name or name.endswith('.log') or path.is_symlink():
                    continue
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                if b'\0' not in data and OLD_NAMES.search(data.decode('utf-8', 'surrogateescape')):
                    yield path


def edit(path, function):
    old = path.read_bytes().decode('utf-8', 'surrogateescape')
    path.write_bytes(function(old).encode('utf-8', 'surrogateescape'))


def find_package(workspace, name):
    """The directory of the package whose package.xml has <name>name</name>, or None."""
    for manifest in sorted((workspace / 'src').rglob('package.xml')):
        if f'<name>{name}</name>' in manifest.read_text(errors='replace'):
            return manifest.parent
    return None


def say(text):
    print(f'\n== {text}', flush=True)


def stack_running():
    out = subprocess.run(['ps', '-eo', 'pid=,args='], stdout=subprocess.PIPE, text=True).stdout
    own = {str(os.getpid()), str(os.getppid())}      # this script's own name contains "rrc_driver"
    rows = (line.split(None, 1) for line in out.splitlines())
    return any(len(r) == 2 and r[0] not in own and re.search(r'ros2 (launch|run)|controller_node|rrc_driver', r[1])
               for r in rows)


def main():
    dry = os.environ.get('DRY_RUN') == '1'
    workspace = Path(os.environ.get('WS') or HOME / 'wro_controller_ws')
    stamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    backup = HOME / f'rename-backup-{stamp}'
    # Only what uses ~/wro_controller_ws. NOT touched: ~/Documents/Testv1 (team archive) and the open-mode stack
    # there, which runs on its own copy of the workspace with the old names (self-consistent).
    extra = [d for d in [HOME / 'scripts'] if d.is_dir()]

    def act(description, function, *args):
        if dry:
            print('DRY:', description)
        else:
            function(*args)

    # 0. checks
    if stack_running():
        print('ROS nodes are running: stop them first (~/scripts/stop_ros.sh).', file=sys.stderr)
        return 1
    driver = find_package(workspace, 'ros_robot_controller')
    messages = find_package(workspace, 'ros_robot_controller_msgs')
    if not driver or not messages:
        print(f'ros_robot_controller / ros_robot_controller_msgs not found under {workspace}/src (already renamed?).',
              file=sys.stderr)
        for name in ('rrc_lite_driver', 'rrc_lite_msgs'):
            print(find_package(workspace, name) or '', file=sys.stderr)
        return 1
    print(f'driver:   {driver}\nmessages: {messages}')

    # 1. backup
    say(f'Backup in {backup}')
    act(f'mkdir {backup}', backup.mkdir)
    act(f'copy {workspace}/src', shutil.copytree, workspace / 'src', backup / 'src', True)
    for folder in extra:
        target = backup / 'extra' / folder.relative_to(folder.anchor)
        act(f'copy {folder}', shutil.copytree, folder, target, True)

    # 2. rename folders and files
    say('Rename folders and files')
    new_driver = driver.parent / 'rrc_lite_driver'
    new_messages = messages.parent / 'rrc_lite_msgs'
    act(f'mv {driver} {new_driver}', driver.rename, new_driver)
    act(f'mv {messages} {new_messages}', messages.rename, new_messages)
    if dry:
        new_driver = driver

    def move_if_there(old, new):
        if old.exists():
            act(f'mv {old} {new}', old.rename, new)

    move_if_there(new_driver / 'ros_robot_controller', new_driver / 'rrc_lite_driver')
    move_if_there(new_driver / 'resource/ros_robot_controller', new_driver / 'resource/rrc_lite_driver')
    package = new_driver / ('ros_robot_controller' if dry else 'rrc_lite_driver')
    move_if_there(package / 'ros_robot_controller_sdk', package / 'rrc_lite_driver_sdk')
    move_if_there(package / 'controller_node.py', package / 'rrc_driver.py')
    move_if_there(new_driver / 'launch/ros_robot_controller.launch.py', new_driver / 'launch/rrc_lite_driver.launch.py')

    # 3. replace names inside text files
    say('Replace names in text files')
    targets = [workspace / 'src', *extra]
    for path in list(text_files(targets)):
        print(path)
        act(f'edit {path}', edit, path, replace_names)
    stop = HOME / 'scripts/stop_ros.sh'
    if stop.is_file() and not dry and STOP_PATTERN_OLD not in stop.read_text():
        # The stop script must keep matching both the old and the new process names.
        edit(stop, lambda t: t.replace("rrc_lite_driver/.*/rrc_driver'",
                                       f"rrc_lite_driver/.*/rrc_driver|{STOP_PATTERN_OLD}'"))
        print(*[line for line in stop.read_text().splitlines() if 'ROS_STACK_PATTERN=' in line], sep='\n')

    node = package / ('controller_node.py' if dry else 'rrc_driver.py')
    if node.is_file():
        say(f'Topics of {node}: ~/x -> rrc/x')
        print(*[line for line in node.read_text(errors='replace').splitlines() if re.search(r'''["']~/''', line)],
              sep='\n')
        act(f'edit topics of {node}', edit, node, private_topics)

    # 4. move old build/install out of the way and rebuild
    say('Old build/install folders -> backup')
    for sub in ('build', 'install'):
        for name in ('ros_robot_controller', 'ros_robot_controller_msgs'):
            old = workspace / sub / name
            if old.exists():
                act(f'mkdir {backup / sub}', lambda d: d.mkdir(parents=True, exist_ok=True), backup / sub)
                act(f'mv {old}', shutil.move, str(old), str(backup / sub / name))
    say('colcon build')
    if not dry:
        build = 'source /opt/ros/jazzy/setup.bash && cd "$1" && colcon build 2>&1 | tail -5'
        subprocess.run(['bash', '-o', 'pipefail', '-c', build, 'bash', str(workspace)], check=True)
        subprocess.run(['systemctl', '--user', 'daemon-reload'], stderr=subprocess.DEVNULL)

    # 5. check
    say('Leftover old names (should be empty)')
    shown = 0
    for path in text_files(targets):
        for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
            if OLD_NAMES.search(line) and STOP_PATTERN_OLD not in line and shown < 20:
                print(f'{path}:{number}:{line}')
                shown += 1
    if not dry:
        print('executables:', flush=True)
        listing = 'source "$1/install/setup.bash" && ros2 pkg executables rrc_lite_driver || true'
        subprocess.run(['bash', '-c', listing, 'bash', str(workspace)])
    print(f'''
Done. Test: ros2 run rrc_lite_driver rrc_driver   then   ros2 topic list | grep /rrc/
Then copy our repository again from the computer and rebuild it (it already uses the new names).

Rollback (nothing was deleted):
  mv {workspace}/src {workspace}/src-renamed-{stamp} && cp -a {backup}/src {workspace}/src
  cp -a {backup}/extra{HOME}/scripts/. {HOME}/scripts/   (the same for Documents/Testv1, .config/systemd/user)
  mv {backup}/install/* {workspace}/install/ ; mv {backup}/build/* {workspace}/build/ ; cd {workspace} && colcon build''')
    return 0


if __name__ == '__main__':
    sys.exit(main())
