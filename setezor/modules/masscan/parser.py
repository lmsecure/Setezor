from setezor.exceptions.loggers import get_logger
import json
import xmltodict
import re
from dataclasses import dataclass
from typing import List, Type, Dict
from abc import abstractstaticmethod


@dataclass
class PortStructure:
    ip: str
    port: int
    state: str
    protocol: str
    ttl: int
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__)
    
    def to_dict(self) -> dict:
        d = self.__dict__
        d.pop('ttl')  #FixMe add ttl to model
        return d
    

@dataclass
class NetworkLink:
    child_ip: str
    parent_ip: str
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__)
    
    def to_dict(self) -> dict:
        return self.__dict__


class BaseMasscanParser:
    
    @abstractstaticmethod
    def parse(input_data: str, parent_ip: str):
        pass


logger = get_logger(__package__, handlers=[])

class XMLParser(BaseMasscanParser):
    
    @staticmethod
    def parse(input_data: str, parent_ip: str) -> List[Type[PortStructure]]:
        port_result: List[Type[PortStructure]] = []
        link_result: List[Type[NetworkLink]] = []
        try:
            json_string_data = json.dumps(xmltodict.parse(input_data))
        except:
            logger.error('XML data parsing error')
            return []
        dict_data = json.loads(re.sub(r'\"@([^"]+)\":', r'"\1":', json_string_data))
        ports_data: List[Dict] = dict_data['nmaprun']['host']
        for i in ports_data:  # ToDo remake to async
            try:
                port_result.append(PortStructure(ip=i['address'].get('addr'),
                                            port=i['ports']['port'].get('portid'),
                                            protocol=i['ports']['port'].get('protocol'),
                                            state=i['ports']['port']['state'].get('state'),
                                            ttl=i['ports']['port']['state'].get('reason_ttl')))
                link_result.append(NetworkLink(child_ip=i['address'].get('addr'),
                                               parent_ip=parent_ip))
            except:
                logger.error(f'Cannot convert to PortStructure next data: {str(i)}')
                continue
        return (port_result, link_result)

class JsonParser(BaseMasscanParser):
    
    @staticmethod
    def parse(input_data: str, parent_ip: str) -> List[Type[PortStructure]]:
        port_result: List[Type[PortStructure]] = []
        link_result: List[Type[NetworkLink]] = []
        try:
            data: List[Dict] = json.loads(input_data)
        except:
            logger.error('Json data parsing error')
            raise Exception("Masscan json log parse error")
        for i in data:  # ToDo remake to async
            try:
                port_result.append(PortStructure(ip=i.get('ip', None),
                                            port=i['ports'][0].get('port', None),
                                            protocol=i['ports'][0].get('proto', None),
                                            state=i['ports'][0].get('status', None),
                                            ttl=i['ports'][0].get('ttl', None)))
                link_result.append(NetworkLink(child_ip=i.get('ip', None),
                                               parent_ip=parent_ip))
            except:
                logger.error(f'Cannot convert to PortStricture next data: {str(i)}')
                continue
        return (port_result, link_result)

class ListParser(BaseMasscanParser):
    
    @staticmethod
    def parse(input_data: str, parent_ip: str) -> List[Type[PortStructure]]:
        if isinstance(input_data, bytes):
            input_data = input_data.decode()
        port_result: List[Type[PortStructure]] = []
        link_result: List[Type[NetworkLink]] = []
        data = [i.split() for i in input_data.splitlines()[1:-1]]
        for i in data:  # ToDo remake to async
            try:
                port_result.append(PortStructure(ip=i[3],
                                            port=int(i[2]),
                                            state=i[0],
                                            protocol=i[1],
                                            ttl=None))
                link_result.append(NetworkLink(child_ip=i[3],
                                               parent_ip=parent_ip))
            except:
                logger.error(f'Cannot convert to PortStricture next data: {str(i)}')
        return (port_result, link_result)