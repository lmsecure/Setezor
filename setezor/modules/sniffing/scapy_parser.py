
from io import BytesIO

from setezor.tools.ip_tools import get_network
from scapy.all import rdpcap
from scapy.plist import PacketList
from setezor.modules.sniffing import packets
from setezor.models import IP, MAC, Route, RouteList, Network



class ScapyParser():

    @classmethod
    def parse_logs(cls, data) -> PacketList:
        file = BytesIO()
        file.seek(0, 2)
        file.write(data)
        file.seek(0)
        pkt_list = cls.read_pcap(file)
        pkts = cls.parse_packets(pkt_list)
        return pkts
    

    @classmethod
    def read_pcap(cls, path: str | BytesIO) -> PacketList:
        """Метод чтения логов захвата траффика в формате pcap

        Args:
            path (str): путь до файла или io.BytesIO

        Returns:
            PacketList: массив пакетов
        """
        try:
            return rdpcap(path)
        except Exception:
            raise Exception('Error with parsing pcal-file. Invalid file format')


    @classmethod
    def parse_packets(cls, pkt_list: PacketList) -> list:
        """Метод парсинга все пакетов, которые были захвачены,
        используя реализованные дочерние классы

        Args:
            pkt_list (PacketList): массив пакетов

        Returns:
            list: массив распарсенных пакетов, которые были захвачены
        """        
        result = []
        for cls in packets.AbstractPacket.__subclasses__():
            result += cls.parse_packet_list(pkt_list)
        return result


    @classmethod
    def restruct_result(cls, data: list[dict], agent_id: int):
        macs_and_ips = dict()
        macs: dict = dict()
        routes = set()
        result = []
        for pkt in data:
            parent_mac = pkt.get('parent_mac').upper()
            parent_ip = pkt.get('parent_ip')
            child_mac = pkt.get('child_mac').upper()
            child_ip = pkt.get('child_ip')
            if (parent_ip, child_ip) not in routes:
                if not (ip_obj := macs_and_ips.get((parent_mac, parent_ip))):
                    if not (new_mac_obj := macs.get(parent_mac)):
                        new_mac_obj = MAC(mac=parent_mac)
                        macs[parent_mac] = new_mac_obj
                    start_ip, broadcast = get_network(ip=parent_ip, mask=24)
                    new_network_obj = Network(start_ip=start_ip, mask=24)
                    parent_ip_obj = IP(ip = parent_ip, mac=new_mac_obj, network=new_network_obj)
                    macs_and_ips.update({(parent_mac, parent_ip) : parent_ip_obj})
                    result.extend([new_mac_obj, new_network_obj, parent_ip_obj])
                else:
                    parent_ip_obj = ip_obj
                if not (ip_obj := macs_and_ips.get((child_mac, child_ip))):
                    if not (new_mac_obj := macs.get(child_mac)):
                        new_mac_obj = MAC(mac=child_mac)
                        macs[child_mac] = new_mac_obj
                    start_ip, broadcast = get_network(ip=child_ip, mask=24)
                    new_network_obj = Network(start_ip=start_ip, mask=24)
                    child_ip_obj = IP(ip = child_ip, mac=new_mac_obj, network=new_network_obj)
                    macs_and_ips.update({(child_mac, child_ip) : child_ip_obj})
                    result.extend([new_mac_obj, new_network_obj, child_ip_obj])
                else:
                    child_ip_obj = ip_obj
                route_obj = Route(agent_id=agent_id)
                result.append(route_obj)
                result.append(RouteList(ip_from=parent_ip_obj, ip_to=child_ip_obj, route=route_obj))
                routes.add((parent_ip, child_ip))
        return result