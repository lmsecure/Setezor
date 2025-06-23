from dataclasses import dataclass, field
from typing import TypedDict    
from typing_extensions import deprecated
import re
import json
import xmltodict
from setezor.models.d_software_type import SoftwareType
from setezor.models.d_software_version import SoftwareVersion
from setezor.tools.ip_tools import get_network

try:
    # from exceptions.loggers import get_logger
    from network_structures import IPv4Struct, PortStruct, SoftwareStruct, RouteStruct
except ImportError:
    # from ...exceptions.loggers import get_logger
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


class NmapParser:
    """Класс парсинга сырых результаов сканирования nmap-а
    """    
    @staticmethod
    def parse_xml(input_xml: str) -> dict:
        """Метод преобразования xml-логов nmap в dict формат

        Args:
            input_xml (str): логи nmap-а в формате xml

        Raises:
            NmapParserError: _description_

        Returns:
            dict: логи nmap-а
        """        
        try:
            tag = '</nmaprun>'
            closed_tag = input_xml[-15:]
            if isinstance(closed_tag, bytes):
                tag = tag.encode()
            if tag not in closed_tag:
                input_xml += tag
            dict_xml = xmltodict.parse(input_xml)
            json_result = json.dumps(dict_xml).replace('@', '')
            # logger.debug('Parse input xml file with size "%s"', len(input_xml if isinstance(input_xml, bytes) else input_xml.encode()))
            return json.loads(json_result)
        except Exception as e:
            raise e
            # logger.error('Failed parse xml file with error\n%s', traceback.format_exc())
            raise Exception('Error with parsing nmap xml-file')
    
    
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
        software_types = {}
        softwares_versions = {}
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
                soft.pop('port', None)
                soft.pop('patch', None)
                soft.pop('platform', None)
                vendor_name = soft.pop('vendor', '') or ""
                if not any(soft.values()):
                    continue
                soft_type_hash_string = soft.pop("type", "") or ""
                product = soft.pop("product", "") or ""
                software_hash_string = vendor_name + product
                version = soft.pop("version", "") or ""
                build = soft.pop("build", "") or ""
                cpe23 = soft.pop("cpe23", "") or ""
                soft_version_hash_string = vendor_name + product + version + build + cpe23

                if vendor_name in vendors:
                    vendor_obj = vendors.get(vendor_name)
                else:
                    vendor_obj = Vendor(name=vendor_name)
                    vendors[vendor_name] = vendor_obj
                    result.append(vendor_obj)
                
                if soft_type_hash_string in software_types:
                    software_type_obj = software_types[soft_type_hash_string]
                else:
                    software_type_obj = SoftwareType(name=soft_type_hash_string)
                    software_types[soft_type_hash_string] = software_type_obj
                    result.append(software_type_obj)

                
                if software_hash_string in softwares:
                    software_obj = softwares[software_hash_string]
                else:
                    software_obj = Software(product=product, vendor=vendor_obj, _type=software_type_obj)
                    softwares[software_hash_string] = software_obj
                    result.append(software_obj)

                if soft_version_hash_string in softwares_versions:
                    soft_version_obj = softwares_versions[soft_version_hash_string]
                else:  
                    soft_version_obj = SoftwareVersion(software=software_obj,
                                                       version=version,
                                                       build=build,
                                                       cpe23=cpe23)
                    softwares_versions[soft_version_hash_string] = soft_version_obj
                    result.append(soft_version_obj)
                L4Software_obj = L4Software(l4=l4_obj, software_version=soft_version_obj, dns_a=dns_a_obj)
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
