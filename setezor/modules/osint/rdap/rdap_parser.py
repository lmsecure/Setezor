from typing import Dict, Any, Optional
from ipaddress import ip_address
from setezor.models.rdap_model import RdapDomain, RdapIpnetwork
from .utils import simplify_rdap_domain, simplify_rdap_ipnetwork
import json
from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.whois_domain import WhoIsDomain
from setezor.models.whois_ip import WhoIsIP
from setezor.tools import ip_tools

class RdapParser:
    @classmethod
    def parse(cls, raw_data: Dict[Any, Any]) -> Optional[Dict[Any, Any]]:
        """
        Валидирует и упрощает RDAP-ответ.
        Выбрасывает исключение при ошибке.
        """
        if not isinstance(raw_data, dict):
            raise ValueError("Raw data must be a dictionary")

        obj_class = raw_data.get("objectClassName", "").lower()
        
        if obj_class == "domain":
            parsed = RdapDomain(**raw_data)
            return simplify_rdap_domain(parsed)
        elif obj_class in ("ip network", "network", "ip"):
            parsed = RdapIpnetwork(**raw_data)
            return simplify_rdap_ipnetwork(parsed)
        else:
            return raw_data 

    @classmethod
    def restructor(cls, data: dict, target: str):
        if not data or not isinstance(data, dict):
            return []

        rdap_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        org_name = cls._extract_org_name(data)

        start = data.get("startAddress")
        end = data.get("endAddress")

        if start and end:
            range_ip = f"{start} - {end}"
        elif start:
            range_ip = start
        elif end:
            range_ip = end
        else:
            range_ip = ""

        domain_crt = data.get("ldhName", target)

        result_data = {
            'data': rdap_json,
            'domain_crt': domain_crt,
            'org_name': org_name,
            'AS': '',
            'range_ip': range_ip,
            'netmask': ''
        }

        output = []

        if ip_tools.is_ip_address(target):
            ip = IP(ip=target)
            output.append(ip)
            obj = WhoIsIP(**result_data, ip=ip)
        else:
            domain = Domain(domain=target)
            output.append(domain)
            obj = WhoIsDomain(**result_data, domain=domain)

        output.append(obj)
        return output

    @staticmethod
    def _extract_org_name(data: dict) -> str:
        entities = data.get("entities", {})
        if not isinstance(entities, dict):
            return ""

        for role in ["registrant", "administrative", "technical", "abuse"]:
            if role in entities:
                for ent in entities[role]:
                    if not isinstance(ent, dict):
                        continue
                    if ent.get("org"):
                        return ent["org"]
                    name = ent.get("name")
                    if isinstance(name, dict) and name.get("default"):
                        return name["default"]
        if data.get("ldhName"):
            return data.get("ldhName")
        return data.get("netname")