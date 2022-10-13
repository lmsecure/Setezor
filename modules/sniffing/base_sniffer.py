from scapy.all import AsyncSniffer, rdpcap, PcapWriter
from scapy.plist import PacketList
from modules.sniffing import packets
from exceptions.loggers import get_logger
from datetime import datetime
import os


logger = get_logger(__package__, handlers=[])

class Sniffer:
    """Класс базового сниффера
    """    

    ## sudo setcap cap_net_raw=eip /usr/bin/pythonX.X
    def __init__(self, iface: str, **kwargs):
        """Инициализация сниффера

        Args:
            iface (str): имя интерфейса для прослушки
        """
        self.iface = iface
        self.sniffer = AsyncSniffer(iface=iface, **kwargs)
        self.log_file_name = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    def start_sniffing(self):
        """Метод запуска захвата траффика
        """        
        self.sniffer.start()
        logger.info('Start sniffer "%s" on interface "%s"', self.__class__.__name__, self.iface)

    def stop_sniffing(self, logs_path: str=None) -> list:
        """Метод остановки захвата траффика парсинга пакетов

        Returns:
            list: массив распарсенных пакетов, которые были захвачены
        """        
        self.sniffer.stop()
        packets = self.sniffer.results
        if logs_path:
            self.save_sniffing_as_pcap(path=logs_path, pkt_list=packets)
        logger.info('Stop sniffer "%s" and capture %s packets', self.__class__.__name__, len(packets))
        # ToDo: save sources by path
        return packets

    def parse_packets(self, pkt_list: PacketList) -> list:
        """Метод парсинга все пакетов, которые были захвачены,
        используя реализованные дочерние классы

        Args:
            pkt_list (PacketList): массив пакетов

        Returns:
            list: массив распарсенных пакетов, которые были захвачены
        """        
        result = []
        logger.debug('Start parse %s packets by %s sniffers', len(pkt_list), len(packets.AbstractPacket.__subclasses__()))
        for cls in packets.AbstractPacket.__subclasses__():
            cls_obj = cls()
            result += cls_obj.parse_packet_list(pkt_list)
        logger.debug('Finished parse %s packets. Can parse %s packets', len(pkt_list), len(result))
        return result

    @staticmethod
    def read_pcap(path: str) -> PacketList:
        """Метод чтения логов захвата траффика в формате pcap

        Args:
            path (str): путь до файла или io.BytesIO

        Returns:
            PacketList: массив пакетов
        """        
        return rdpcap(path)

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