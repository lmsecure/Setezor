from tasks.scapy_scan_task import ScapyScanTask
from modules.sniffing.base_sniffer import Sniffer
from database.queries import Queries
from .base_job import BaseJob, CustomScheduler, MessageObserver
import io
import traceback
import asyncio
from tools.ip_tools import get_self_ip


class ScapyLogTask(ScapyScanTask):
    
    def __init__(self, observer: MessageObserver, scheduler: CustomScheduler, name: str, db: Queries, data: str, scapy_logs: str, iface: str, task_id: int):
        super(ScapyScanTask, self).__init__(observer=observer, scheduler=scheduler, name=name, update_graph=False)
        self.db = db
        self.iface = iface
        self._coro = self.run(data=data, scapy_logs=scapy_logs, task_id=task_id)
        
    async def parse_pkt_list(self, data: str, scapy_logs:str):
        sniffer = Sniffer('parse', None, log_path=scapy_logs)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sniffer.read_pcap, io.BytesIO(data))
        await loop.run_in_executor(None, sniffer.save_sniffing_as_pcap, scapy_logs, result)
        return await loop.run_in_executor(None, sniffer.parse_packets, result)
    
    async def run(self, data: str, scapy_logs: str, task_id: int):
        try:
            parsed_pkt_list = await self.parse_pkt_list(data=data, scapy_logs=scapy_logs)
            self.db.l3link.write_many(data=[{'start_ip': get_self_ip(self.iface).get('ip'), **pkt} for pkt in parsed_pkt_list], to_update=False)
            self.logger.debug('Parse pcap file and extract information from %s packets', len(parsed_pkt_list))
            self.db.task.set_finished_status(index=task_id)
        except Exception as e:
            self.db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            self.logger.error('Fail with parse pcap-file. Error stacktrace:\n%s', traceback.format_exc())
            raise e