import socket
import fcntl
import struct
import ipaddress
from setezor.network_structures import InterfaceStruct

    
def get_default_interface():
    return ''


def get_ipv4(interface: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', interface.encode()[:15]))[20:24])


def get_mac(interface: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return ':'.join('%02x' % b for b in fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(interface, 'utf-8')[:15]))[18:24]).upper()
        

def get_interfaces() -> list[InterfaceStruct]:
    
    """Возвращает список интерфейсов"""
    
    ifaces = []
    for ind, name in socket.if_nameindex():
        try:
            ip = get_ipv4(name)
        except Exception:
            ip = None
        try:
            mac = get_mac(name)
        except Exception:
            mac = None
        ifaces.append(InterfaceStruct(
            name=name,
            ip=ip,
            mac=mac
            ))
    return ifaces


def is_ip_address(address):
        try:
            socket.inet_aton(address)
            return True
        except OSError:
            return False


def get_network(ip: str, mask: int) -> tuple[str:, str]:
    """ Функция получения инвормации о подсети по ip и маске

    Returns:
        tuple: (start_ip, broadcast)
    """

    network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
    start_ip = str(network.network_address)
    broadcast = str(network.broadcast_address)
    return start_ip, broadcast