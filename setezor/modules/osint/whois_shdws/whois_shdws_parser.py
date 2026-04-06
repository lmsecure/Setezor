import ipaddress
from typing import Dict, List, Any, Optional

from setezor.tools import ip_tools

from setezor.models import ASN, Network, IP



class WhoisShdwsParser:

    @classmethod
    def parse(cls, raw_data: Dict[Any, Any], target: str) -> Optional[Dict[Any, Any]]:
        result: dict = {}

        if not raw_data or not ip_tools.is_ip_address(target):
            return result
        result.update({"ip": target})

        cidr = raw_data.get('CIDR') or raw_data.get('route', '')
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

        result.update({
            "network": {
                "start_ip": start_ip,
                "end_ip": end_ip,
                "mask": mask
            }
        })

        org_candidates = [
            raw_data.get('OrgName'),
            raw_data.get('org', ''),
            raw_data.get('Organization', ''),
            raw_data.get('organization', '')
        ]
        for org_name in org_candidates:
            if org_name: break

        asn_candidates = [
            raw_data.get('ASN'),
            raw_data.get('OriginAS'),
            raw_data.get('origin', '')
        ]
        for asn_number in asn_candidates:
            if asn_number: break

        result.update({
            "asn": {
                "name": raw_data.get('NetName', ''),
                "number": asn_number,
                "org": org_name,
                "country": raw_data.get('Country', '')
            }
        })

        return result


    @classmethod
    def restructor(cls, data: dict) -> List:
        if not data:
            return []
        asn_obj = ASN(**data.get("asn"))
        network_obj = Network(**data.get("network"), asn=asn_obj)
        ip_obj = IP(ip=data.get("ip"), network=network_obj)
        return [ip_obj, network_obj, asn_obj]
