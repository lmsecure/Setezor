from tasks.base_task import BaseTask
from modules.sniffing.base_sniffer import Sniffer
from tools.ip_tools import get_self_ip
from database.queries import Queries
import asyncio


class ScapyScanTask(BaseTask):
        
    async def _task_func(self, iface: str, scapy_logs: str, timeout: float=30,  *args, **kwargs):
        sniffer = Sniffer(iface=iface)
        sniffer.start_sniffing()
        await asyncio.sleep(timeout)
        packets = sniffer.stop_sniffing(logs_path=scapy_logs)
        return sniffer.parse_packets(packets)
    
    def _write_result_to_db(self, db: Queries, result: list, iface: str, *args, **kwargs):
        self_addr = get_self_ip(iface)
        # FixMe transform sniffing results to format which comfortable to write to db
        for i in result:
            if any(['ip' in j for j in list(i.keys())]):
                db.l3link.write(start_ip=self_addr.get('ip'), **i)
            else:
                db.mac.write(i.get('child_mac'))
                db.mac.write(i.get('parent_mac'))