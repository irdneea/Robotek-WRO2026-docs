"""Network settings of a Mac that talks to the real car over Wi-Fi (used by car_bag_mac.py and macos_rviz_real.py)."""
import re
import subprocess

DEFAULT_IP = '192.168.0.10'     # a placeholder: set PI_IP to the address of your car


def interface(pi_ip):
    try:
        out = subprocess.run(['route', '-n', 'get', pi_ip], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True).stdout
    except OSError:
        return ''
    found = re.search(r'interface:\s*(\S+)', out)
    return found.group(1) if found else ''


def environment(base):
    """``base`` (the macOS environment) with the car's network. Returns (env, car address, network interface).

    macos_env leaves the Mac in domain 42 with discovery on this machine only (for the simulation): with that the Mac
    sees no node of the Pi. Cyclone DDS and Fast DDS did not see each other in the test of 9 Oct 2026.
    """
    env = dict(base)
    pi_ip = env.get('PI_IP') or DEFAULT_IP
    env['RMW_IMPLEMENTATION'] = env.get('REAL_CAR_RMW') or 'rmw_cyclonedds_cpp'
    env['ROS_DOMAIN_ID'] = env.get('REAL_CAR_DOMAIN_ID') or '1'
    env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'SUBNET'
    env['ROS_STATIC_PEERS'] = env.get('ROS_STATIC_PEERS') or pi_ip     # unicast discovery besides multicast
    name = ''
    if env['RMW_IMPLEMENTATION'] == 'rmw_cyclonedds_cpp':
        name = interface(pi_ip)
        if name:
            env['CYCLONEDDS_URI'] = (f'<CycloneDDS><Domain><General><Interfaces><NetworkInterface name="{name}" '
                                     'multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General>'
                                     '</Domain></CycloneDDS>')
    return env, pi_ip, name
