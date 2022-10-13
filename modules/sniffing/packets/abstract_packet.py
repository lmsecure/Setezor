from abc import ABC, abstractmethod, abstractstaticmethod
from scapy.packet import Packet
from scapy.plist import PacketList



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
    
    def parse_packet_list(self, pkt_list: PacketList) -> list:
        """Метод парсинга захваченных пакетов

        Args:
            pkt_list (PacketList): массив пакетов

        Returns:
            list: массив распарсенных пакетов
        """        
        result = []
        for pkt in pkt_list:
            if self.is_packet_type(pkt):
                parsed_packet = self.parse_packet(pkt)
                if parsed_packet:
                    result.append(parsed_packet)
        return result


