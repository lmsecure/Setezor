from scapy.layers.l2 import LLC
from scapy.packet import Packet
from exceptions.loggers import get_logger
from .abstract_packet import AbstractPacket


logger = get_logger(__package__, handlers=[])


class NetBOISPacket(AbstractPacket):
    """Класс для работы с netbios пакетами
    """

    @staticmethod
    def parse_packet(pkt: Packet) -> dict:
        """Метод парсига netbios пакета

        Args:
            pkt (Packet): пакет

        Returns:
            dict: распарсенный пакет
        """        
        res = None
        # try:
        #     res.update({'parent_mac': pkt['Dot3'].src})
        #     res.update({'child_mac': pkt['Dot3'].dst})
        # except:
        #     logger.error('Cannot parse package %s by "%s"', str(pkt), NetBOISPacket.__name__)
        return res

    @staticmethod
    def is_packet_type(pkt: Packet) -> bool:
        """метод проверки наличия информации об netbios 

        Args:
            pkt (Packet): пакет

        Returns:
            bool: _description_
        """        
        return LLC in pkt.layers()