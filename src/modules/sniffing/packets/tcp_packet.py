from scapy.layers.inet import TCP, UDP
from scapy.packet import Packet
from exceptions.loggers import get_logger
from .abstract_packet import AbstractPacket


logger = get_logger(__package__, handlers=[])


class TCPPacket(AbstractPacket):
    """Класс для работы с tcp пакетами
    """    
    @staticmethod
    def parse_packet(pkt: Packet) -> dict:
        """Метод парсига tcp пакета

        Args:
            pkt (Packet): пакет

        Returns:
            dict: распарсенный пакет
        """        
        res = {}
        try:
            res.update({'parent_mac': pkt['Ether'].src, 'parent_ip': pkt['IP'].src})
            res.update({'child_mac': pkt['Ether'].dst, 'child_ip': pkt['IP'].dst, })
        except:
            logger.error('Cannot parse package %s by "%s"', pkt.summary(), TCPPacket.__name__)
        return res

    @staticmethod
    def is_packet_type(pkt: Packet) -> bool:
        """метод проверки наличия информации об tcp 

        Args:
            pkt (Packet): пакет

        Returns:
            bool: _description_
        """        
        return TCP in pkt.layers() or UDP in pkt.layers()
