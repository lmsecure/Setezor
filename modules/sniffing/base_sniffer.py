from scapy.all import AsyncSniffer, rdpcap, PcapWriter, wrpcap
from scapy.plist import PacketList, Packet
from modules.sniffing import packets
from exceptions.loggers import get_logger
from datetime import datetime
import os
from typing import Callable
import traceback
import asyncio


logger = get_logger(__package__, handlers=[])

class Sniffer:
    """Класс базового сниффера
    """    

    ## sudo setcap cap_net_raw=eip /usr/bin/pythonX.X
    def __init__(self, iface: str, write_packet_to_db: Callable, log_path: str):
        """Инициализация сниффера

        Args:
            iface (str): имя интерфейса для прослушки
        """
        self.iface = iface
        self.sniffer = AsyncSniffer(iface=iface, prn=self.print_func)
        self.log_file_name = os.path.join(log_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.pcap')
        self.write_packet_to_db: Callable = write_packet_to_db
        
    def start_sniffing(self):
        """Метод запуска захвата траффика
        """
        try:
            self.sniffer.start()
            logger.info('Start sniffer "%s" on interface "%s"', self.__class__.__name__, self.iface)
        except:
            raise Exception('Error with starting sniffer by interface %s' % self.iface)

    def stop_sniffing(self) -> None:
        """Метод остановки захвата траффика парсинга пакетов

        Returns:
            list: массив распарсенных пакетов, которые были захвачены
        """
        try:
            self.sniffer.stop()
            logger.info('Stop sniffer "%s"', self.__class__.__name__)
        except:
            raise Exception('Error in stoping sniffer. Maybe sniffer not started?')

    def print_func(self, pkt: Packet):
        try:
            parsed_packet = self.parse_packet(pkt)
            self.write_packet_to_db(parsed_packet)
            self.write_packet_to_file(pkt)
        except Exception as e:
            logger.error(f'Cannot parse packet, write to db or file. Packet info: {e}')
            print(traceback.format_exc())
        
    def write_packet_to_file(self, pkt, append=True):
        wrpcap(self.log_file_name, pkt, append=append)
    
    def parse_packets(self, pkt_list: PacketList) -> list:
        """Метод парсинга все пакетов, которые были захвачены,
        используя реализованные дочерние классы

        Args:
            pkt_list (PacketList): массив пакетов

        Returns:
            list: массив распарсенных пакетов, которые были захвачены
        """        
        result = []
        logger.debug('Start parse %s packets by %s packet analyzers', len(pkt_list), len(packets.AbstractPacket.__subclasses__()))
        for cls in packets.AbstractPacket.__subclasses__():
            result += cls.parse_packet_list(pkt_list)
            
        logger.debug('Finished parse %s packets. Can parse %s packets', len(pkt_list), len(result))
        return result
    
    def parse_packet(self, pkt: Packet):
        for cls in packets.AbstractPacket.__subclasses__():
            cls_obj = cls()
            if cls_obj.is_packet_type(pkt):
                return cls_obj.parse_packet(pkt)

    @staticmethod
    def read_pcap(path: str) -> PacketList:
        """Метод чтения логов захвата траффика в формате pcap

        Args:
            path (str): путь до файла или io.BytesIO

        Returns:
            PacketList: массив пакетов
        """
        try:
            return rdpcap(path)
        except:
            raise Exception('Error with parsing pcal-file. Invalid file format')

    def save_sniffing_as_pcap(self, path: str, pkt_list: PacketList, append: bool=True):
        """Метод сохранения захваченных пакетов в pcap формате

        Args:
            path (str): путь до файда
            pkt_list (PacketList): массив пакетов
            append (bool, optional): режим дозаписи пакетов в лог файл
        """        
        logger.info(f'Save scapy source packet to file by path "{path}"')
        writer = PcapWriter(os.path.join(path, f'{self.log_file_name}.pcap'), append=append, sync=True)
        writer.write(pkt_list)
        logger.debug(f'Write to "{path}" {len(pkt_list)} packages')