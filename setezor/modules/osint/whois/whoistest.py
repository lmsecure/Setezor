import json
from typing import TypedDict
import socket
import time
from datetime import datetime
from ipaddress import IPv4Address, AddressValueError
from pprint import pprint

from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.whois_domain import WhoIsDomain
from setezor.models.whois_ip import WhoIsIP
from setezor.tools import ip_tools

# class WhoisResult(TypedDict):
    
#     domain: str

# res = WhoisResult(domain='test.ru')
# res['']

class Whois:

    @classmethod
    def socket_connect(cls, addr, ip):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, 43))
        s.send((ip + "\r\n").encode())
        response = b""
        while True:
            data = s.recv(4096)
            response += data
            if not data:
                break
        s.close() 
        return response
    
    @classmethod
    def ianna(cls, ip:str):
        '''
            Используется для получения информации о регистраторе IP-адреса
        '''
        addr = "whois.iana.org"
        response = cls.socket_connect(addr, ip)
        whois = ''
        for resp in response.decode().splitlines():
            if resp.startswith('%') or not resp.strip():
                continue
            elif resp.startswith('whois'):
                whois = resp.split(":")[1].strip()
                break
        return whois
    
    @classmethod
    def parse_whois_info(cls, whois_info):
        whois_ip = dict()  
        for ln in whois_info.decode().splitlines():
            if ln.strip().startswith("%") or not ln.strip():
                continue
            else:
                pair = ln.strip().split(": ")
                if len(pair) != 2:
                    continue
                key, value = pair[0].strip(), pair[1].strip()
                if dict_value := whois_ip.get(key,False):
                    if isinstance(dict_value,list):
                        whois_ip[key].append(value)
                    else:
                        whois_ip[key] = [dict_value,value]
                else:
                    whois_ip[key] = value
        return whois_ip
    
    @classmethod
    def get_whois(cls, ip:str):      
        try:
            if whois := cls.ianna(ip):
                if info := cls.parse_whois_info(cls.socket_connect(whois,ip)):
                    return info
            else:
                if info := cls.parse_whois_info(cls.socket_connect(ip,'www.whois.com')):
                    return info
        except AddressValueError:
            print("IP-address not valid")
        except ConnectionResetError as ex:
            print(ex)

    @classmethod
    def restruct_result(self, target, result: dict):
            data = dict()
            output = []
            data.update({'data': json.dumps(result),
                        'domain_crt': result.get('domain', target),
                        'org_name': result.get('org', ''),
                        'AS': '',
                        'range_ip': '',
                        'netmask': ''})
            alias_org_name = ['OrgName', 'Organization', 'organization']
            alias_range = ['NetRange', 'inetnum']
            alias_netmask = ['CIDR', 'route']
            alias_origin = ['OriginAS', 'origin']
            for org_name in alias_org_name:
                if org_name in result:
                    data.update({'org_name': result[org_name]})
                    break
            for _origin in alias_origin:
                if _origin in result:
                    data.update({'AS': result[_origin]})
                    break
            for _range in alias_range:
                if _range in result:
                    data.update({'range_ip': result[_range]})
            for _net_mask in alias_netmask:
                if _net_mask in result:
                    # _netmask = result[i].split('/')[1]
                    #print(_net_mask)
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