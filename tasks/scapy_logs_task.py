from tasks.scapy_scan_task import ScapyScanTask
from modules.sniffing.base_sniffer import Sniffer
from tools.ip_tools import get_self_ip
from database.queries import Queries
import io
from base64 import b64decode


class ScapyLogTask(ScapyScanTask):
        
    async def _task_func(self, log_file: str, scapy_logs:str, *args, **kwargs):
        pcap = b64decode(log_file.split(',')[1])
        sniffer = Sniffer('test')
        result = sniffer.read_pcap(io.BytesIO(pcap))
        sniffer.save_sniffing_as_pcap(path=scapy_logs, pkt_list=result)
        return sniffer.parse_packets(result)