#!/usr/bin/env python3
"""USB map of the Pi 5: which device hangs from which xHCI controller, at what speed and with which stable name.

Read only. Run it on the Pi, or from another computer:  ssh <user>@<car-address> python3 - < tools/pi_usb_map.py
To know which physical port is each controller: plug ONE device into a port, run it, note the controller
(xhci-hcd.0 or .1) and the row (bus/port); repeat for the four ports.
"""
import glob
import os
import re
import subprocess

SYS = os.environ.get('ROBOTEK_SYSFS', '/sys/bus/usb/devices')
DEV = os.environ.get('ROBOTEK_DEV', '/dev')
CURRENT = os.environ.get('ROBOTEK_MAX_CURRENT', '/proc/device-tree/chosen/power/max_current')


def read(path):
    try:
        with open(path, errors='replace') as f:
            return f.read().strip()
    except OSError:
        return ''


def devices():
    for path in sorted(glob.glob(os.path.join(SYS, '[0-9]*-[0-9]*'))):
        name = os.path.basename(path)
        if ':' in name or '.' in name or not os.path.isfile(os.path.join(path, 'idVendor')):
            continue
        controller = re.search(r'xhci-hcd\.[0-9]', os.path.realpath(path))
        yield (name, f"{read(path + '/idVendor')}:{read(path + '/idProduct')}", read(path + '/speed'),
               controller.group(0) if controller else '?', read(path + '/product'))


def stable_names():
    for folder in ('serial/by-id', 'v4l/by-id'):
        for link in sorted(glob.glob(os.path.join(DEV, folder, '*'))):
            if os.path.islink(link):
                yield os.path.basename(link), os.readlink(link)


def max_current():
    """The current in mA that the power supply offers: four bytes, big-endian (0 if it cannot be read)."""
    try:
        with open(CURRENT, 'rb') as f:
            return int.from_bytes(f.read(4), 'big')
    except OSError:
        return 0


def main():
    row = '%-6s %-10s %-6s %-11s %s'
    print(row % ('PORT', 'USB_ID', 'MB/s', 'CONTROLLER', 'PRODUCT'))
    for device in devices():
        print(row % device)
    print('\nStable names (they do not change with the port):')
    for name, target in stable_names():
        print(f'  {name} -> {target}')
    try:
        setting = subprocess.run(['vcgencmd', 'get_config', 'usb_max_current_enable'], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, text=True).stdout.strip()
    except OSError:
        setting = ''
    print(f'\nCurrent: supply {max_current()} mA, {setting}')


if __name__ == '__main__':
    main()
