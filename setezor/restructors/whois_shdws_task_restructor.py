import json
import orjson
from setezor.models.ip import IP
from setezor.models.asn import ASN
from setezor.models.network import Network
from setezor.tools import ip_tools
import ipaddress

class WhoisShdwsTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, target: str, **kwargs):
        if not raw_result or not ip_tools.is_ip_address(target):
            return []

        org_candidates = [
            raw_result.get('OrgName'),
            raw_result.get('org', ''),
            raw_result.get('Organization', ''),
            raw_result.get('organization', '')
        ]
        org_name = next((v for v in org_candidates if v), '')

        asn_candidates = [
            raw_result.get('ASN'),
            raw_result.get('OriginAS'),
            raw_result.get('origin', '')
        ]
        asn_number = next((v for v in asn_candidates if v), '')

        cidr = raw_result.get('CIDR') or raw_result.get('route', '')
        start_ip = end_ip = ''
        mask = 24
        if cidr and '/' in cidr:
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                start_ip = str(net.network_address)
                end_ip = str(net.broadcast_address)
                mask = net.prefixlen
            except ValueError:
                pass
        
        ip_obj = IP(ip=target)

        network_obj = Network(
            start_ip=start_ip,
            end_ip=end_ip,
            mask=mask,
            ips=[ip_obj]
        )

        asn_obj = ASN(
            name=raw_result.get('NetName', ''),
            number=asn_number,
            org=org_name,
            country=raw_result.get('Country', ''),
            networks=[network_obj]
        )

        return [asn_obj, network_obj, ip_obj]

    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)