import json
from typing import TypedDict
import socket
import time
from datetime import datetime
from ipaddress import IPv4Address, AddressValueError
from pprint import pprint

# class WhoisResult(TypedDict):
    
#     domain: str

# res = WhoisResult(domain='test.ru')
# res['']

class Whois():
    @staticmethod
    def socket_connect(addr, ip):
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
    
    @staticmethod
    def ianna(ip):
        '''
            Используется для получения информации о регистраторе IP-адреса
        '''
        addr = "whois.iana.org"
        response = Whois.socket_connect(addr, ip)
        whois = ''
        for resp in response.decode().splitlines():
            if resp.startswith('%') or not resp.strip():
                continue
            elif resp.startswith('whois'):
                whois = resp.split(":")[1].strip()
                break
        return whois
    
    @staticmethod
    def parse_whois_info(whois_info):
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
    
    @staticmethod
    def get_whois(ip):      
        try:
            if whois := Whois.ianna(ip):
                if info := Whois.parse_whois_info(Whois.socket_connect(whois,ip)):
                    return info
            else:
                if info := Whois.parse_whois_info(Whois.socket_connect(ip,'www.whois.com')):
                    return info
        except AddressValueError:
            print("IP-address not valid")
        except ConnectionResetError as ex:
            print(ex)

