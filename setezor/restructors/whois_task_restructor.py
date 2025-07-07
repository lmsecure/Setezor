import json

import orjson
from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.whois_domain import WhoIsDomain
from setezor.models.whois_ip import WhoIsIP
from setezor.tools import ip_tools

class WhoisTaskRestructor:
    @classmethod
    async def restruct(cls, raw_result, target: str, **kwargs):
        data = dict()
        output = []
        data.update({'data': json.dumps(raw_result),
                    'domain_crt': raw_result.get('domain', target),
                    'org_name': raw_result.get('org', ''),
                    'AS': '',
                    'range_ip': '',
                    'netmask': ''})
        alias_org_name = ['OrgName', 'Organization', 'organization']
        alias_range = ['NetRange', 'inetnum']
        alias_netmask = ['CIDR', 'route']
        alias_origin = ['OriginAS', 'origin']
        for org_name in alias_org_name:
            if org_name in raw_result:
                data.update({'org_name': raw_result[org_name]})
                break
        for _origin in alias_origin:
            if _origin in raw_result:
                data.update({'AS': raw_result[_origin]})
                break
        for _range in alias_range:
            if _range in raw_result:
                data.update({'range_ip': raw_result[_range]})
        for _net_mask in alias_netmask:
            if _net_mask in raw_result:
                break
        if ip_tools.is_ip_address(target):
            ip = IP(ip=target)
            output.append(ip)
            obj = WhoIsIP(**data, ip=ip)
        else:
            domain = Domain(domain=target)
            output.append(domain)
            obj = WhoIsDomain(**data, domain=domain)
        output.append(obj)
        return output
    
    @classmethod
    def get_raw_result(cls, data):
        return orjson.dumps(data)