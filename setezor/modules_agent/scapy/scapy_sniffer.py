from scapy.all import AsyncSniffer, PcapWriter
from scapy.plist import PacketList, Packet
import traceback
from io import BytesIO



class PcapWriterNoClose(PcapWriter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def __exit__(self, exc_type, exc_value, tracback):
        pass



class ScapySniffer:

    ## sudo setcap cap_net_raw=eip /usr/bin/pythonX.X
    def __init__(self, iface: str):
        """Инициализация сниффера

        Args:
            iface (str): имя интерфейса для прослушки
        """
        self.iface = iface
        self.result_pkts: PacketList = []
        self.result_file = BytesIO()
        self.sniffer = AsyncSniffer(iface=iface, prn=self.print_func)


    def start_sniffing(self):
        """Метод запуска захвата траффика
        """
        try:
            self.sniffer.start()
        except Exception:
            raise Exception('Error with starting sniffer by interface %s' % self.iface)


    def stop_sniffing(self) -> PacketList:
        """Метод остановки захвата траффика парсинга пакетов
        
        Returns:
            PacketList: массив распарсенных пакетов, которые были захвачены
        """
        try:
            self.sniffer.stop()
            return self.save_sniffing_as_pcap()
        except Exception:
            raise Exception('Error in stoping sniffer. Maybe sniffer not started?')


    def print_func(self, pkt: Packet):
        try:
            self.result_pkts.append(pkt)
        except Exception as e:
            print(traceback.format_exc())


    def save_sniffing_as_pcap(self):
        with PcapWriterNoClose(self.result_file) as fdesc:
            for pkt in self.result_pkts:
                fdesc.write(pkt)
        result = self.result_file.getvalue()
        self.result_file.close()
        return result
