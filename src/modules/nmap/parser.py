from dataclasses import dataclass, field
from typing import TypedDict    
from typing_extensions import deprecated
    
try:
    from exceptions.loggers import get_logger
    from tools.xml_utils import XMLParser
    from network_structures import IPv4Struct, PortStruct, ServiceStruct, RouteStruct
except ImportError:
    from ...exceptions.loggers import get_logger
    from ...tools.xml_utils import XMLParser
    from ...network_structures import IPv4Struct, PortStruct, ServiceStruct, RouteStruct

logger = get_logger(__package__, handlers=[])

class NmapRunResult(TypedDict):

    addresses: list[IPv4Struct]
    traces: list[IPv4Struct]

@dataclass(slots=True)
class NmapStructure:
    """Структура для хранения распарсенных результатов
    """
    addresses: list = field(default_factory=list)
    hostnames: list  = field(default_factory=list)
    ports: list = field(default_factory=list)
    traces: list[RouteStruct] = field(default_factory=list)


class NmapParser(XMLParser):
    """Класс парсинга сырых результаов сканирования nmap-а
    """    

    @classmethod
    def to_list(csl, data: dict | list) -> list:
        """Если на вход принимает словарь - преобразует его в лист

        Args:
            data (dict or list): данные

        Returns:
            list: данные в виде list
        """        
        '''
        
        '''
        if data is None:
            return []
        return [data] if not isinstance(data, list) else data

    @classmethod
    def parse_addresses(cls, address: list | dict) -> list:
        """Метод парсинга раздела с адресами

        Args:
            address (list or dict): информация из раздела с адресами

        Returns:
            list: распарсенные данные об адресах
        """        
        address = NmapParser.to_list(address)
        if address:
            return [{f'{i.get("addrtype").replace("v4", "")}': i.get('addr') for i in address}]
        else: 
            return []

    @classmethod
    def parse_hostname(cls, hostnames: list | dict) -> list:
        """Метод парсинга раздела с именем хоста

        Args:
            hostnames (list or dict):  информация из раздела с именами машин

        Returns:
            list: распарсенные данные об именах машин
        """        
        hostnames = NmapParser.to_list(hostnames)
        if hostnames:
            return [', '.join([j.get('name') for i in hostnames for j in NmapParser.to_list(i.get('hostname'))])]
        else:
            return [None]

    @classmethod
    def parse_traces(cls, trace: list | dict, agent_id: int, 
                     self_address: IPv4Struct, host: IPv4Struct) -> list:
        """Метод парсинга раздела с трассировки хоста

        Args:
            trace (list or dict): информация из раздела с трассировкой
            self_address (dict): адреса сетевого интерфейса машины, с которой производилось сканирование (где запущено приложение)

        Returns:
            list: распарсенные данные о трассировках
        """        
        trace = NmapParser.to_list(trace.get('hop') if trace else None)
        addresses = [IPv4Struct.model_validate(i) for i in trace]
        if not addresses:
            addresses = [self_address, host]
        else:
            addresses.insert(0, self_address)
        route = RouteStruct(agent_id=agent_id, routes=addresses)
        return route
    
    
    @classmethod
    @deprecated('Нужно будет перейти на структуры')
    def _parse_traces(cls, trace: list | dict, self_address: dict) -> list:
        trace = NmapParser.to_list(trace.get('hop') if trace else None)
        result = []
        if trace:
            for index, i in enumerate(trace):
                if index == 0:
                    result.append({'parent_ip': self_address.get('ip'), 'child_ip': i.get('ipaddr'),
                                   'parent_mac': self_address.get('mac'), 'child_mac': i.get('mac'),
                                   'parent_name': self_address.get('name'), 'child_name': i.get('host'), 'start_ip': self_address.get('ip')})
                    pass
                if index == len(trace) - 1:
                    continue
                else:
                    result.append({'parent_ip': i.get('ipaddr'), 'child_ip': trace[index + 1].get('ipaddr'),
                                   'parent_mac': i.get('mac'), 'child_mac': trace[index + 1].get('mac'),
                                   'parent_name': i.get('host'), 'child_name': trace[index + 1].get('host')})
        return result

    @classmethod
    def parse_ports(cls, ports: dict | list, address: dict) -> list:
        """Метод парсинга раздела с результатами сканирования портов

        Args:
            ports (dict or list): информация из раздела с портами
            address (dict): адреса сканируемой машины

        Returns:
            list: распарсенные данные о портах
        """        
        result: list[PortStruct] = []
        ports = NmapParser.to_list(ports.get('port') if ports else None)
        if ports:
            for i in ports:
                service = i.get('service')
                if service:
                        result.append({'port': i.get('portid'), 'ip': address.get('ip'),
                                       'mac': address.get('mac'), 'service_name': service.get('name'),
                                       'product': service.get('product'), 'extra_info': service.get('extrainfo'),
                                       'version': service.get('version'), 'os_type': service.get('ostype'),
                                       'cpe': ', '.join(service.get('cpe')) if isinstance(service.get('cpe'), list) else service.get('cpe'),
                                       'state': i.get('state').get('state'), 'protocol': i.get('protocol')})
        return result
    
    @classmethod
    def convert_to_structures(cls, res: NmapStructure):
        from time import time
        # todo! Придумать что делать c ipv6
        addresses = [IPv4Struct.model_validate(i) for i in res.addresses]
        ports = {i['ip']:[] for i in res.ports}
        for i in res.ports:
            port = PortStruct.model_validate(i)
            if 'service_name' in i:
                service = ServiceStruct.model_validate(i)
                port.service = service
            ports[i['ip']].append(port)
        for addr in addresses:
            addr.ports = ports[str(addr.address)]
        return NmapRunResult({'addresses': addresses, 'traces': res.traces})
    
    def parse_hosts(self, scan: dict, agent_id: int, self_address: IPv4Struct | None | dict = None):
        """Метод парсинга лога nmap-а

        Args:
            scan (dict): информация о сканировании
            self_address (dict): адреса сетевого интерфейса машины, с которой производилось сканирование (где запущено приложение)

        Returns:
            NmapStructure: _description_
        """        
        result = NmapStructure()
        if 'nmaprun' in scan:
            scan = scan['nmaprun']
        hosts = self.to_list(scan.get('host'))
        if len(hosts) == 0:
            hosts = self.to_list(scan.get('hosthint'))
        logger.debug('Start parse %s hosts', len(hosts))
        for h in hosts:
            address_data = self.parse_addresses(h.get('address'))
            hostname_data = self.parse_hostname(h.get('hostnames'))
            trace_data = self.parse_traces(h.get('trace'), agent_id, self_address, IPv4Struct.model_validate(address_data[0]))
            for index, i in enumerate(address_data):
                i.update({'domain_name': hostname_data[index]})
            ports_data = self.parse_ports(h.get('ports'), address_data[0])
            result.addresses += address_data
            result.hostnames += hostname_data
            result.ports += ports_data
            result.traces.append(trace_data)
        logger.debug('Finish parse %s hosts. Get %s addresses, %s hostnames, %s ports, %s traces', 
                     len(hosts), *[len(result.__getattribute__(i)) for i in result.__slots__])
        # res = self.convert_to_structures(result)
        return result