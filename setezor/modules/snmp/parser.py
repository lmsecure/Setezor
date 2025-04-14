
from base64 import b64decode

from setezor.tools.ip_tools import get_network
from setezor.models import Authentication_Credentials, Port, IP, Network, DNS_A, Domain



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
            domain_obj = Domain()
            dns_a_obj = DNS_A(target_domain=domain_obj, target_ip=ip_obj)
            port_obj = Port(port=port, ip=ip_obj)
            result.extend([network_obj, ip_obj, port_obj, domain_obj, dns_a_obj])
            for item in data:
                result.append(Authentication_Credentials(port=port_obj, **item))
        return result
