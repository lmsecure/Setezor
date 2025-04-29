import orjson
from setezor.models import ip
from setezor.models.auth_credentials_resource import Authentication_Credentials
from setezor.models.dns_a import DNS_A
from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.network import Network
from setezor.models.port import Port
from setezor.tools.ip_tools import get_network


class SnmpTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, target_ip: str, target_port: str):
        result = []
        if raw_result:
            start_ip, broadcast = get_network(ip=target_ip, mask=24)
            network_obj = Network(start_ip = start_ip, mask=24)
            ip_obj = IP(ip=target_ip, network=network_obj)
            domain_obj = Domain()
            dns_a_obj = DNS_A(target_domain=domain_obj, target_ip=ip_obj)
            port_obj = Port(port=target_port, protocol="udp", ip=ip_obj)
            result.extend([network_obj, ip_obj, port_obj, domain_obj, dns_a_obj])
            for item in raw_result:
                result.append(Authentication_Credentials(port=port_obj, **item))
        return result
