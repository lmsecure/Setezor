from abc import ABC, abstractmethod, abstractstaticmethod
from scapy.packet import Packet
from scapy.plist import PacketList
import asyncio



class AbstractPacket(ABC):
    
    @abstractstaticmethod
    def is_packet_type(pkt: Packet):
        """Метод опредления пакета

        Args:
            pkt (Packet): пакет
        """        
        pass
    
    @abstractstaticmethod
    def parse_packet(pkt: Packet):
        """Метод парсинга пакета

        Args:
            pkt (Packet): пакет
        """        
        pass
    
    @classmethod
    def parse_packet_list(cls, pkt_list: PacketList) -> list:
        """Метод парсинга захваченных пакетов

        Args:
            pkt_list (PacketList): массив пакетов

        Returns:
            list: массив распарсенных пакетов
        """        
        result = []
        for pkt in pkt_list:
            if cls.is_packet_type(pkt):
                parsed_packet = cls.parse_packet(pkt)
                if parsed_packet and parsed_packet not in result:
                    result.append(parsed_packet)
        return result


