import os
import re
from tools.shell_tools import create_shell_subprocess
import socket
import fcntl
import struct


def get_self_ip(iface: str):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', iface.encode()[:15]))[20:24])
    except:
        raise Exception('Can not get IP address for iface %s' % iface)
    
    
def get_self_interfaces():
    return os.listdir('/sys/class/net')


