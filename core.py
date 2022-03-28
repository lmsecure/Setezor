from database.queries import (
    get_or_add_ip,
    get_or_add_mac,
    get_or_add_object,
    get_or_add_l3_link,
    get_or_add_port
)
from scan.active_scan.nmap_scanning import NmapScanner
from scan.passive_scan.sniffers import (
    ARPSniffer,
    LLMNRSniffer,
    TCPSniffer,
    NetBOISSniffer,
    Sniffer)
from multipledispatch import dispatch
from database.db_connection import DBConnection
import os
import re


class Core:
    def __init__(self, iface: str):
        self.iface = iface
        self.nmap_scanner = NmapScanner()
        self.sniffers = [ARPSniffer(iface), LLMNRSniffer(iface), TCPSniffer(iface), NetBOISSniffer(iface)]

    @dispatch(str, str)
    def active_scan(self, target: str, scan_type: str):
        result = self.nmap_scanner.universal_scan(target, scan_type)
        self.nmap_scan_to_db(result.get('nmaprun'))

    @dispatch(str)
    def active_scan(self, command: str):
        result = self.nmap_scanner.interactive_scan(command)
        r = self.nmap_scan_to_db(result.get('nmaprun'))
        return r

    @staticmethod
    def get_self_ip(iface):
        log = os.popen(f'ifconfig {iface}').read()
        my_ip = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', log)[0]
        my_mac = re.findall(
            r'ether ([0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2})',
            log)[0]
        return {'ip': my_ip, 'mac': my_mac}

    def nmap_scan_to_db(self, scan: dict):
        def to_list(data):
            return [data] if isinstance(data, dict) else data
        if not scan:
            return []
        address_data = []
        hostname_data = []
        trace_data = []
        ports_data = []
        self_address = self.get_self_ip(self.iface)
        for h in to_list(scan.get('host')):
            address = to_list(h.get('address'))
            hostnames = to_list(h.get('hostnames'))
            trace = h.get('trace')
            ports = h.get('ports')
            tmp_address = {}
            if address:
                for i in address:
                    tmp_address.update({f'{i.get("addrtype").replace("v4", "")}': i.get('addr')})
                address_data.append(tmp_address)
            if hostnames:
                hostname_data.append(', '.join([i.get('hostname').get('name') for i in hostnames]))
            else:
                hostname_data.append(None)
            if trace:
                trace = to_list(trace.get('hop'))
                if trace:
                    for index, i in enumerate(trace):
                        if index == 0:
                            trace_data.append({'parent_ip': self_address.get('ip'), 'child_ip': i.get('ipaddr'),
                                               'parent_mac': self_address.get('mac'), 'child_mac': i.get('mac'),
                                               'parent_name': self_address.get('name'), 'child_name': i.get('host')})
                        if index == len(trace) - 1:
                            continue
                        else:
                            trace_data.append({'parent_ip': i.get('ipaddr'), 'child_ip': trace[index + 1].get('ipaddr'),
                                               'parent_mac': i.get('mac'), 'child_mac': trace[index + 1].get('mac'),
                                               'parent_name': i.get('host'), 'child_name': trace[index + 1].get('host')})
            if ports:
                ports = to_list(ports.get('port'))
                if ports:
                    for i in ports:
                        service = i.get('service')
                        if service:
                            ports_data.append({'port': i.get('portid'),
                                               'ip': tmp_address.get('ip'),
                                               'mac': tmp_address.get('mac'),
                                               'service': service.get('name'),
                                               'product': service.get('product'),
                                               'extra_info': service.get('extrainfo'),
                                               'version': service.get('version'),
                                               'os_type': service.get('ostype'),
                                               'cpe': ', '.join(service.get('cpe')) if isinstance(service.get('cpe'), list)
                                                                                    else service.get('cpe'),
                                               'state': i.get('state').get('state')})

        ses = DBConnection().create_session()
        for i in trace_data:
            get_or_add_l3_link(ses, **i)
        # print(ports_data)
        for i in ports_data:
            r1 = get_or_add_port(ses, **i)
        for index, i in enumerate(address_data):
            r2 = get_or_add_ip(ses, ip=i.get('ip'), mac=i.get('mac'), domain_name=hostname_data[index])
        ses.commit()
        return scan

    def start_passive_scan(self):
        [i.start_sniffing() for i in self.sniffers]
        return True

    def stop_passive_scan(self):
        result = []
        for i in self.sniffers:
            sniffer_result = i.stop_sniffing()
            result += sniffer_result
        self.scapy_scan_to_db(result)

    def parse_nmap_xml_log(self, xml_log_path: str):
        xml_data = open(xml_log_path, 'r').read()
        result = self.nmap_scanner.parse_xml(xml_data)
        self.nmap_scan_to_db(result)

    def parse_pcap_log(self, pcap_log_path: str):
        result = Sniffer(self.iface).parse_packets_list(pcap_log_path)
        self.scapy_scan_to_db(result)

    def scapy_scan_to_db(self, scan: list):
        ses = DBConnection().create_session()
        for i in scan:
            if any(['ip' in j for j in list(i.keys())]):
                get_or_add_l3_link(ses, **i)
            else:
                get_or_add_mac(ses, i.get('child_mac'))
                get_or_add_mac(ses, i.get('parent_mac'))
        ses.commit()
