import asyncio
import json
import xmltodict
import re

from setezor.tools.ip_tools import get_network
from setezor.models import IP, Port, MAC, Network


class BaseMasscanParser:
    
    async def parse(input_data: str):
        pass

    @classmethod
    async def _parser_results(cls, format: str, input_data: str):
        parsers: dict = {
            'xml': XMLParser,
            'oX': XMLParser,
            'json': JsonParser,
            'oJ': JsonParser,
            'list': ListParser,            
            'oL': ListParser,
        }
        loop = asyncio.get_event_loop()
        parser = parsers.get(format)
        return await parser.parse(input_data=input_data)
    
    @classmethod
    async def restruct_result(cls, data: dict, agent_id: int, interface_ip_id: int):
        result = []
        ips_objs = dict()
        for ip_target, ports_target in data.items():
            if not (ip_obj := ips_objs.get(ip_target, None)):
                start_ip, broadcast = get_network(ip = ip_target, mask = 24)
                network_obj = Network(start_ip=start_ip, mask=24)
                ip_obj = IP(ip=ip_target, network=network_obj)
                ips_objs.update({ip_target : ip_obj})
                result.extend([network_obj, ip_obj])
                for port in ports_target:
                    port_obj = Port(ip=ip_obj, **port)
                    result.append(port_obj)
        return result


class XMLParser(BaseMasscanParser):
    
    @classmethod
    async def parse(cls, input_data: str) -> dict[str, list]:
        if not input_data:
            raise Exception("Masscan xml log file empty")
        port_result = dict()
        try:
            json_string_data = json.dumps(xmltodict.parse(input_data))
        except:
            raise Exception("Masscan xml log parse error")
        dict_data = json.loads(re.sub(r'\"@([^"]+)\":', r'"\1":', json_string_data))
        ports_data: list[dict] = dict_data['nmaprun']['host']
        for i in ports_data:
            try:
                if i['address'].get('addr') not in port_result:
                    port_result[i['address'].get('addr')] = []
                port_result[i['address'].get('addr')].append({
                    "port": i['ports']['port'].get('portid'),
                    "protocol": i['ports']['port'].get('protocol'),
                    "state": i['ports']['port']['state'].get('state'),
                    "ttl": i['ports']['port']['state'].get('reason_ttl')})
            except:
                continue
        return port_result


class JsonParser(BaseMasscanParser):
    
    @classmethod
    async def parse(cls, input_data: str) -> dict[str, list]:
        if not input_data:
            raise Exception("Masscan json log file empty")
        port_result = dict()
        try:
            data: list[dict] = json.loads(input_data)
        except:
            raise Exception("Masscan json log parse error")
        for i in data:
            try:
                if i.get('ip', None):
                    if i.get('ip') not in port_result:
                        port_result[i.get('ip')] = []
                    port_result[i.get('ip', None)].append({
                        "port": i['ports'][0].get('port', None),
                        "protocol": i['ports'][0].get('proto', None),
                        "state": i['ports'][0].get('status', None),
                        "ttl": i['ports'][0].get('ttl', None)})
            except:
                continue
        return port_result


class ListParser(BaseMasscanParser):
    
    @classmethod
    async def parse(cls, input_data: str) -> dict[str, list]:
        if not input_data:
            raise Exception("Masscan list log file empty")
        if isinstance(input_data, bytes):
            input_data = input_data.decode()
        port_result = dict()
        data = [i.split() for i in input_data.splitlines()[1:-1]]
        for i in data:
            try:
                if i[3] not in port_result:
                    port_result[i[3]] = []
                port_result[i[3]].append({
                    "port": int(i[2]),
                    "state": i[0],
                    "protocol": i[1],
                    "ttl": None})
            except:
                raise Exception("Masscan list log parse error")
        return port_result