import asyncio
import socket
import fcntl
import struct

from pyroute2 import IPDB

from setezor.network_structures import InterfaceStruct


# ipdb = IPDB() # эта хуйня при инициализации создает 2 сокета и 4 пайпа
# Так же поиск занимает около 0.03 сек, что при постоянном использовании может влиять на производительность,
# Поэтому интерфейс выбирается при запуске приложения
with  IPDB() as db:
    DEFAULT_INTERFACE = db.interfaces[db.routes['default']['oif']]['ifname']
    
def get_default_interface():
    return DEFAULT_INTERFACE

def get_ipv4(interface: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', interface.encode()[:15]))[20:24])


def get_mac(interface: str):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return ':'.join('%02x' % b for b in fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(interface, 'utf-8')[:15]))[18:24])
        

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
            id=ind,
            name=name,
            ip_address=ip,
            mac_address=mac
            ))
    return ifaces

def is_ip_address(address):
        try:
            socket.inet_aton(address)
            return True
        except OSError:
            return False

async def get_ip_by_domain_name(name) -> str:
    try:
        result = await asyncio.get_running_loop().getaddrinfo(
            name,
            80,
            type=socket.SOCK_STREAM,
            flags=socket.AI_ADDRCONFIG,
            family=socket.AF_INET
        )
        return result[0][4][0]
    except:
        return None