
from base64 import b64decode

from setezor.tools.ip_tools import get_network
from setezor.models import L7_Authentication_Credentials, L7, Port, IP, Network



class SnmpParser:

    @classmethod
    def parse_community_strings_file(cls, file) -> set:
        if not file:
            return []
        data = b64decode(file.split(',')[1]).decode()
        return set(data.splitlines())

    @classmethod
    def restruct_result(cls, ip: str, port: int, data: list[dict]):
        result = []
        if data:
            start_ip, broadcast = get_network(ip=ip, mask=24)
            network_obj = Network(start_ip = start_ip, mask=24)
            ip_obj = IP(ip=ip, network=network_obj)
            port_obj = Port(port=port, ip=ip_obj)
            l7_obj = L7(port=port_obj)
            result.extend([network_obj, ip_obj, port_obj, l7_obj])
            for item in data:
                result.append(L7_Authentication_Credentials(l7=l7_obj, **item))
        return result
