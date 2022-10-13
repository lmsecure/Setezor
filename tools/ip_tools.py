import os
import re
from tools.shell_tools import create_shell_subprocess


def get_self_ip(iface: str):
        res, err = create_shell_subprocess(f'ifconfig {iface}'.split()).communicate()
        if err:
            pass  # Todo: raise exception
        ip = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', res)
        mac = re.findall(
            r'ether ([0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2})',
            res)
        my_ip = ip[0] if ip else None
        my_mac = mac[0] if mac else None
        return {'ip': my_ip, 'mac': my_mac}
    
    
def get_self_interfaces():
    return os.listdir('/sys/class/net')


