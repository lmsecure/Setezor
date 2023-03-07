from exceptions.loggers import get_logger


logger = get_logger(__package__, handlers=[])


class NmapStructure:
    """Структура для хранения распарсенных результатов
    """
    __slots__ = ['addresses', 'hostnames', 'traces', 'ports']
    def __init__(self):
        self.addresses = []
        self.hostnames  = []
        self.ports = []
        self.traces = []


class NmapParser:
    """Класс парсинга сырых результаов сканирования nmap-а
    """    

    @staticmethod
    def to_list(data: dict or list) -> list:
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

    @staticmethod
    def parse_addresses(address: list or dict) -> list:
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

    @staticmethod
    def parse_hostname(hostnames: list or dict) -> list:
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

    @staticmethod
    def parse_traces(trace: list or dict, self_address: dict) -> list:
        """Метод парсинга раздела с трассировки хоста

        Args:
            trace (list or dict): информация из раздела с трассировкой
            self_address (dict): адреса сетевого интерфейса машины, с которой производилось сканирование (где запущено приложение)

        Returns:
            list: распарсенные данные о трассировках
        """        
        result = []
        trace = NmapParser.to_list(trace.get('hop') if trace else None)
        if trace:
            for index, i in enumerate(trace):
                if index == 0:
                    result.append({'parent_ip': self_address.get('ip'), 'child_ip': i.get('ipaddr'),
                                   'parent_mac': self_address.get('mac'), 'child_mac': i.get('mac'),
                                   'parent_name': self_address.get('name'), 'child_name': i.get('host'), 'start_ip': self_address.get('ip')})
                if index == len(trace) - 1:
                    continue
                else:
                    result.append({'parent_ip': i.get('ipaddr'), 'child_ip': trace[index + 1].get('ipaddr'),
                                   'parent_mac': i.get('mac'), 'child_mac': trace[index + 1].get('mac'),
                                   'parent_name': i.get('host'), 'child_name': trace[index + 1].get('host'), 'start_ip': self_address.get('ip')})
        return result

    @staticmethod
    def parse_ports(ports: dict or list, address: dict) -> list:
        """Метод парсинга раздела с результатами сканирования портов

        Args:
            ports (dict or list): информация из раздела с портами
            address (dict): адреса сканируемой машины

        Returns:
            list: распарсенные данные о портах
        """        
        result = []
        ports = NmapParser.to_list(ports.get('port') if ports else None)
        if ports:
            for i in ports:
                service = i.get('service')
                if service:
                        result.append({'port': i.get('portid'), 'ip': address.get('ip'),
                                       'mac': address.get('mac'), 'service': service.get('name'),
                                       'product': service.get('product'), 'extra_info': service.get('extrainfo'),
                                       'version': service.get('version'), 'os_type': service.get('ostype'),
                                       'cpe': ', '.join(service.get('cpe')) if isinstance(service.get('cpe'), list) else service.get('cpe'),
                                       'state': i.get('state').get('state'), 'protocol': i.get('protocol')})
        return result
    
    def parse_hosts(self, scan: dict, self_address: dict) -> NmapStructure:
        """Метод парсинга лога nmap-а

        Args:
            scan (dict): информация о сканировании
            self_address (dict): адреса сетевого интерфейса машины, с которой производилось сканирование (где запущено приложение)

        Returns:
            NmapStructure: _description_
        """        
        result = NmapStructure()
        hosts = self.to_list(scan.get('host'))
        if len(hosts) == 0:
            hosts = self.to_list(scan.get('hosthint'))
        logger.debug('Start parse %s hosts', len(hosts))
        for h in hosts:
            address_data = self.parse_addresses(h.get('address'))
            hostname_data = self.parse_hostname(h.get('hostnames'))
            trace_data = self.parse_traces(h.get('trace'), self_address)
            if not trace_data:
                for i in address_data:
                    if i.get('ip') != self_address.get('ip'):
                        trace_data.append({'parent_ip': self_address.get('ip'), 'child_ip': i.get('ip'), 'start_ip': self_address.get('ip')})
            for index, i in enumerate(address_data):
                i.update({'domain_name': hostname_data[index]})
            ports_data = self.parse_ports(h.get('ports'), address_data[0])
            result.addresses += address_data
            result.hostnames += hostname_data
            result.ports += ports_data
            result.traces += trace_data
        logger.debug('Finish parse %s hosts. Get %s addresses, %s hostnames, %s ports, %s traces', 
                     len(hosts), *[len(result.__getattribute__(i)) for i in result.__slots__])
        return result