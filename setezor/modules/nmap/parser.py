from dataclasses import dataclass, field
from typing import TypedDict    
from typing_extensions import deprecated
import re
import json

from setezor.tools.ip_tools import get_network

try:
    # from exceptions.loggers import get_logger
    from tools.xml_utils import XMLParser
    from network_structures import IPv4Struct, PortStruct, SoftwareStruct, RouteStruct
except ImportError:
    # from ...exceptions.loggers import get_logger
    from ...tools.xml_utils import XMLParser
    from ...network_structures import IPv4Struct, PortStruct, SoftwareStruct, RouteStruct

from cpeguess.cpeguess import CPEGuess

from setezor.models import IP, Port, Software, L4Software, MAC, Vendor, Route, RouteList, Network, DNS_A, Domain

# logger = get_logger(__package__, handlers=[])



class NmapRunResult(TypedDict):

    addresses: list[IPv4Struct]
    traces: list[IPv4Struct]

@dataclass(slots=True)
class NmapStructure:
    """Структура для хранения распарсенных результатов
    """
    addresses: list = field(default_factory=list)
    hostnames: list  = field(default_factory=list)
    ports: dict = field(default_factory=dict)
    softwares: dict = field(default_factory=dict)
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
            list: распарсенных данных о портах
        """
        result: list[PortStruct] = []
        ports = NmapParser.to_list(ports.get('port') if ports else None)
        if ports:
            for port in ports:
                if (tunnel := port.get('service', {}).get('tunnel')):
                    if tunnel != "ssl": # TODO
                        print("If you see this message, please notify the developer:")
                        print("no \"ssl\" tunnel detected:", tunnel)
                result.append({'port': int(port.get('portid')),
                               'mac': address.get('mac'), 'service_name' : port.get('service', {}).get('name'),
                                'state': port.get('state', {}).get('state'),
                                'protocol': port.get('protocol'),
                                'is_ssl' : tunnel == "ssl"})

        return result



    @classmethod
    def parse_softwares(cls, ports : dict | list, address : dict) -> list:
        """Метод парсинга раздела с результатами сканирования софта

        Args:
            ports (dict or list): информация из раздела с портами
            address (dict): адреса сканируемой машины

        Returns:
            list: распарсенные данные о софте портов
        """
        # SoftwareStruct:
        # vendor :      # 
        # product :     # service -> product
        # type :        # Software
        # version :     # service -> version
        # build :       # 
        # patch :       # 
        # platform :    # отдельной структурой
        # cpe23 :       # service -> cpe
        result: list[SoftwareStruct] = []
        ports = NmapParser.to_list(ports.get('port'))
        if ports:
            for port in ports:
                tmp_soft = {}
                service = port.get('service', "")
                if service:
                    cpe = service.get('cpe', "")

                    cpe_type = ""
                    vendor = service.get('vendor', "")
                    product = service.get('product', "")
                    version = service.get('version', "")
                    if version: version = re.search("([0-9]{1,}[.]){0,}[0-9]{1,}", version).group(0)

                    if cpe:
                        if isinstance(service.get('cpe'), list):
                            list_cpe = [i.replace('/', '2.3:') for i in cpe if i.replace('/', '2.3:').count(':') >= 5]
                            cpe = list_cpe[0] if len(list_cpe) == 1 else ', '.join(list_cpe) or ""
                        else: # str
                            cpe = cpe.replace('/', '2.3:')

                        if cpe and len(cpe.split(', ')) == 1:
                            vendor = cpe.split(':')[3]
                            product = cpe.split(':')[4]
                            cpe_type = {'a' : 'Applications', 'h' : 'Hardware', 'o' : 'Operating Systems'}.get(cpe.split(':')[2])
                            if cpe.count(':') < 5:
                                if version:
                                    cpe += ':' + version.split()[0]
                                else:
                                    cpe = ""
                            else:
                                if not version:
                                    version = cpe.split(':')[5]

                    if product and version:
                        list_cpe = CPEGuess.search(vendor=vendor, product=product, version=version, exact=True)
                        cpe = ', '.join(list_cpe) if list_cpe else ""
                    else:
                        cpe = ', '.join(service.get('cpe')) if isinstance(service.get('cpe'), list) else service.get('cpe', "")

                    tmp_soft.update({'port' : port.get('portid'),
                                     'vendor' : vendor or "",
                                     'product' : product or "",
                                     'type' : cpe_type,
                                     'version' : version or "",
                                     'cpe23' : cpe or ""})
                result.append(tmp_soft)
        return result


    @classmethod
    def convert_to_structures(cls, res: NmapStructure):
        from time import time
        # todo! Придумать что делать c ipv6
        addresses = [IPv4Struct.model_validate(i) for i in res.addresses]
        ports = {i['ip']:[] for i in res.ports}
        for i in res.ports:
            port = PortStruct.model_validate(i)
            ports[i['ip']].append(port)
        for addr in addresses:
            addr.ports = ports[str(addr.address)]
        return NmapRunResult({'addresses': addresses, 'traces': res.traces})

    def parse_hosts(self, scan: dict, agent_id: int, self_address: IPv4Struct | None | dict = None) -> tuple[NmapStructure, bool]:
        """Метод парсинга лога nmap-а

        Args:
            scan (dict): информация о сканировании
            self_address (dict): адреса сетевого интерфейса машины, с которой производилось сканирование (где запущено приложение)

        Returns:
            NmapStructure: _description_
        """
        result = NmapStructure()
        traceroute = "-traceroute" in scan.get('args', "")
        if 'nmaprun' in scan:
            scan = scan['nmaprun']
        hosts = self.to_list(scan.get('host'))
        if len(hosts) == 0:
            hosts = self.to_list(scan.get('hosthint'))
        # logger.debug('Start parse %s hosts', len(hosts))
        uniq_addrs = set()
        for h in hosts:
            address_data = self.parse_addresses(h.get('address'))
            if json.dumps(address_data) not in uniq_addrs:
                uniq_addrs.add(json.dumps(address_data) )
                hostname_data = self.parse_hostname(h.get('hostnames'))
                trace_data = self.parse_traces(h.get('trace'), agent_id, self_address, IPv4Struct.model_validate(address_data[0]))
                for index, i in enumerate(address_data):
                    i.update({'domain_name': hostname_data[index]})
                ports_data = self.parse_ports(h.get('ports',{}), address_data[0])
                software_data = self.parse_softwares(h.get('ports',{}), address_data[0])
                result.addresses += address_data
                result.hostnames += hostname_data
                result.ports.update({address_data[0].get('ip') : ports_data})
                result.softwares.update({address_data[0].get('ip')  : software_data})
                result.traces.append(trace_data)

        return result, traceroute

    @classmethod
    def restruct_result(cls, data, interface_ip_id: int, traceroute: bool) -> list:
        result = []
        address_in_traceses = dict()
        vendors = {}
        softwares = {}
        empty_vendor = Vendor(name='')
        vendors[''] = empty_vendor
        result.append(empty_vendor)
        for i in range(len(data.addresses)):
            mac_obj = MAC(mac=data.addresses[i].get('mac', ''), vendor=empty_vendor)
            result.append(mac_obj)
            start_ip, broadcast = get_network(ip=data.addresses[0].get('ip'), mask=24)
            network_obj = Network(start_ip=start_ip, mask=24)
            result.append(network_obj)
            ip_obj = IP(ip=data.addresses[i].get('ip'), mac=mac_obj, network=network_obj)
            result.append(ip_obj)
            domain_obj = Domain()
            result.append(domain_obj)
            dns_a_obj = DNS_A(target_ip=ip_obj, target_domain=domain_obj)
            result.append(dns_a_obj)
            address_in_traceses[ip_obj.ip] = ip_obj
            ports = data.ports.get(data.addresses[i].get('ip'), [])
            softs = data.softwares.get(data.addresses[i].get('ip'), [])
            for port, soft in zip(ports, softs):
                l4_obj = Port(ip=ip_obj, **port)
                result.append(l4_obj)
                if any([v for k, v in soft.items() if k != 'port']):
                    soft.pop('port', None)
                    vendor_name = soft.pop('vendor', '')
                    if vendor_name in vendors:
                        vendor_obj = vendors.get(vendor_name)
                    else:
                        vendor_obj = Vendor(name=vendor_name)
                        vendors[vendor_name] = vendor_obj
                        result.append(vendor_obj)

                    hash_string = vendor_name or "_" + "_".join([v for v in soft.values() if v])

                    if not (hash_string and hash_string in softwares):
                        soft_obj = Software(vendor=vendor_obj, **soft)
                        softwares[hash_string] = soft_obj
                        result.append(soft_obj)
                        L4Software_obj = L4Software(l4=l4_obj, software=soft_obj, dns_a=dns_a_obj)
                        result.append(L4Software_obj)
        if traceroute:
            for i in range(len(data.addresses)):
                froms_tos = []
                for r in data.traces[i].routes[1:-1]:
                    start_ip, broadcast = get_network(ip=str(r.address), mask=24)
                    if not (ip_obj_in_trace := address_in_traceses.get(str(r.address))):
                        network_obj = Network(start_ip=start_ip, mask=24)
                        result.append(network_obj)
                        ip_obj_in_trace = IP(ip=str(r.address), network=network_obj)
                        result.append(ip_obj_in_trace)
                        domain_obj = Domain()
                        result.append(domain_obj)
                        dns_a_obj = DNS_A(target_ip=ip_obj_in_trace, target_domain=domain_obj)
                        result.append(dns_a_obj)
                        froms_tos.append(str(r.address))
                        address_in_traceses.update({str(r.address) : ip_obj_in_trace})
                    else:
                        froms_tos.append(str(r.address))
                froms_tos.append(data.addresses[i].get('ip'))
                route_obj = Route(agent_id=data.traces[i].agent_id)
                result.append(route_obj)
                result.append(RouteList(ip_id_from=interface_ip_id, ip_to=address_in_traceses[froms_tos[0]], route=route_obj))
                for i in range(1, len(froms_tos)):
                    result.append(RouteList(ip_from=address_in_traceses[froms_tos[i-1]], 
                                            ip_to=address_in_traceses[froms_tos[i]], route=route_obj))
        return result
