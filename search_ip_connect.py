import socket
from scapy.all import ARP, Ether, srp
from logging_prog import *

def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    subnet = local_ip.rsplit('.', 1)[0] + '.0/24'
    logger.info(f"Detected local IP: {local_ip}")
    return subnet


def scan_all_devices(subnet=None, iface=None):
    if subnet is None:
        subnet = get_local_subnet()

    if iface:
        print(f"Using interface: {iface}")
    else:
        print("Using default network interface.")

    arp = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    # More verbose output for debugging
    result = srp(packet, timeout=3, verbose=1, iface=iface)[0] if iface else srp(packet, timeout=3, verbose=1)[0]
    devices = []

    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})


    if not devices:
        logger.info("No devices found.\n\nTroubleshooting tips:\n- Run with sudo.\n- Check your subnet and interface.\n- Ensure devices are active.\n- Try specifying iface='eth0' or your wifi interface name.\n- Try pinging a device manually before scanning.")
    return devices


