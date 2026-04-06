from setezor.models import IP, DNS, Domain, Network, Port, Authentication_Credentials
from setezor.tools.ip_tools import get_network
from setezor.db.entities import DNSTypes



class SNMP_Parser:

    @classmethod
    async def restruct(cls, raw_result, target_ip: str, target_port: str):
        result = []
        if raw_result:
            start_ip, broadcast = get_network(ip=target_ip, mask=24)
            network_obj = Network(start_ip = start_ip, mask=24)
            ip_obj = IP(ip=target_ip, network=network_obj)
            port_obj = Port(port=target_port, protocol="udp", ip=ip_obj)
            result.extend([network_obj, ip_obj, port_obj])
            for item in raw_result:
                result.append(Authentication_Credentials(port=port_obj, **item))
        return result
