from scapy.all import AsyncSniffer, rdpcap, wrpcap
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.l2 import ARP, LLC
from scapy.layers.llmnr import LLMNRQuery
from scapy.plist import PacketList
from scapy.packet import Packet
from datetime import datetime
from config import ScapyConfig
from abc import abstractmethod
from exceptions.exception_logger import exception_decorator
from exceptions.loggers import LoggerNames, get_logger


class Sniffer:

    def __init__(self, iface: str, **kwargs):
        self.logger = get_logger(LoggerNames.scan)
        self.iface = iface
        self.sniffer = AsyncSniffer(iface=iface, **kwargs)

    def start_sniffing(self):
        self.sniffer.start()
        self.logger.info(f'Start sniffer "{self.__class__.__name__}"')

    def stop_sniffing(self):
        self.sniffer.stop()
        self.logger.info(f'Stop sniffer')
        if ScapyConfig.default_source_path:
            self.save_sniffing_as_pcap(ScapyConfig.default_source_path, self.sniffer.results,
                                       type=self.__class__.__name__.replace('Sniffer', ''))
        return self.parse_packets_list(self.sniffer.results)

    def parse_packets_list(self, pcap_path):
        pkt_list = self.read_pcap(pcap_path)
        result = []
        for cls in Sniffer.__subclasses__():
            cls_obj = cls(self.iface)
            result += cls_obj.parse_packets_list(pkt_list)
        return result

    def _parse_packet_list(self, pkt_list: PacketList):
        result = []
        for pkt in pkt_list:
            if self.is_packet_type(pkt):
                parsed_packet = self.parse_packet(pkt)
                if parsed_packet:
                    result.append(parsed_packet)

    @abstractmethod
    def parse_packet(self, pkt: Packet):
        pass

    @staticmethod
    def read_pcap(path):
        return rdpcap(path)

    def save_sniffing_as_pcap(self, path, pkt_list: PacketList, **kwargs):
        full_path = f'{path}/{datetime.now()}_{kwargs.get("type") + "_" if kwargs.get("type") else ""}scapy.pcap'
        self.logger.info(f'Save scapy source packet to file by path "{full_path}"')
        wrpcap(full_path, pkt_list)

    @staticmethod
    @abstractmethod
    def is_packet_type(pkt: Packet):
        pass


class ARPSniffer(Sniffer):
    def __init__(self, iface: str):
        super().__init__(iface, filter='arp')

    @staticmethod
    @exception_decorator(LoggerNames.scan, False)
    def parse_packet(self, pkt: Packet):
        res = {}
        res.update({'parent_mac': pkt['ARP'].hwsrc, 'parent_ip': pkt['ARP'].psrc})
        res.update({'child_mac': pkt['ARP'].hwdst, 'child_ip': pkt['ARP'].pdst})
        return res

    def parse_packets_list(self, pkt_list: PacketList):
        return self._parse_packet_list(pkt_list)

    @staticmethod
    def is_packet_type(pkt: Packet):
        return ARP in pkt.layers()


class LLMNRSniffer(Sniffer):
    def __init__(self, iface: str):
        super().__init__(iface, filter='udp port 5355')

    @staticmethod
    @exception_decorator(LoggerNames.scan, False)
    def parse_packet(pkt: Packet):
        res = {}
        res.update({'parent_mac': pkt['Ether'].src, 'parent_ip': pkt['IP'].src})
        res.update({'child_mac': pkt['Ether'].dst, 'child_ip': pkt['IP'].dst})
        return res

    def parse_packets_list(self, pkt_list: PacketList):
        return self._parse_packet_list(pkt_list)

    @staticmethod
    def is_packet_type(pkt: Packet):
        return LLMNRQuery in pkt.layers()


class NetBOISSniffer(Sniffer):
    def __init__(self, iface: str):
        super().__init__(iface, filter='llc')

    @staticmethod
    @exception_decorator(LoggerNames.scan, False)
    def parse_packet(self, pkt: Packet):
        res = {}
        res.update({'parent_mac': pkt['Dot3'].src})
        res.update({'child_mac': pkt['Dot3'].dst})
        return res

    def parse_packets_list(self, pkt_list: PacketList):
        return self._parse_packet_list(pkt_list)

    @staticmethod
    def is_packet_type(pkt: Packet):
        return LLC in pkt.layers()


class TCPSniffer(Sniffer):
    def __init__(self, iface: str):
        super().__init__(iface, filter='tcp or udp')

    @staticmethod
    @exception_decorator(LoggerNames.scan, False)
    def parse_packet(self, pkt: Packet):
        res = {}
        res.update({'parent_mac': pkt['Ether'].src, 'parent_ip': pkt['IP'].src})
        res.update({'child_mac': pkt['Ether'].dst, 'child_ip': pkt['IP'].dst, })
        return res

    def parse_packets_list(self, pkt_list: PacketList):
        return self._parse_packet_list(pkt_list)

    @staticmethod
    def is_packet_type(pkt: Packet):
        return TCP in pkt.layers() or UDP in pkt.layers()
