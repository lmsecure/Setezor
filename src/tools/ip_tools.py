from dataclasses import dataclass, asdict
import socket
import fcntl
import struct

from pyroute2 import IPDB


@dataclass(slots=True, order=True)
class Interface:
    
    id: int
    name: str
    ip_address: str | None = None
    mac_address: str | None = None
    default: bool = False
    
    def to_dict(self):
        return asdict(self)

def get_default_interface():
    
    ip = IPDB()
    res = ip.interfaces[ip.routes['default']['oif']]
    return res['ifname']


def get_ipv4(interface: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', interface.encode()[:15]))[20:24])


def get_mac(interface: str):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return ':'.join('%02x' % b for b in fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(interface, 'utf-8')[:15]))[18:24])
        

def get_interfaces():
    
    """Возвращает список интерфейсов"""
    
    ifaces: list[Interface] = []
    default_iface = get_default_interface()
    default_i = None
    for ind, name in socket.if_nameindex():
        if name == default_iface:
            default = True
        else:
            default = False
        
        try:
            ip = get_ipv4(name)
        except Exception:
            ip = None
            
        try:
            mac = get_mac(name)
        except Exception:
            mac = None
        
        if default:
            default_i = Interface(ind, name, ip, mac, default)
        else:
            ifaces.append(Interface(ind, name, ip, mac, default))
    
    ifaces.sort(key=lambda x: x.id)
    if default_i:
        ifaces.insert(0, default_i)
    return ifaces
