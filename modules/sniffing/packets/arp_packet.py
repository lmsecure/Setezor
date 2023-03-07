from scapy.layers.l2 import ARP
from scapy.packet import Packet
from exceptions.loggers import get_logger
from .abstract_packet import AbstractPacket


logger = get_logger(__package__, handlers=[])


class ARPPacket(AbstractPacket):
    """Класс для работы с ARP пакетами
    """

    @staticmethod
    def parse_packet(pkt: Packet) -> dict:
        """Метод парсига arp пакета

        Args:
            pkt (Packet): пакет

        Returns:
            dict: распарсенный пакет
        """
        res = {}
        try:
            res.update({'parent_mac': pkt['ARP'].hwsrc, 'parent_ip': pkt['ARP'].psrc})
            res.update({'child_mac': pkt['ARP'].hwdst, 'child_ip': pkt['ARP'].pdst})
        except:
            logger.error('Cannot parse package %s by "%s"', pkt.summary(), ARPPacket.__name__)
        return res

    @staticmethod
    def is_packet_type(pkt: Packet) -> bool:
        """метод проверки наличия информации об arp 

        Args:
            pkt (Packet): пакет

        Returns:
            bool: _description_
        """        
        return ARP in pkt.layers() # haslayer()
