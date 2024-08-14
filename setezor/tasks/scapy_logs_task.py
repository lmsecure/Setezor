from setezor.tasks.scapy_scan_task import ScapyScanTask
from setezor.modules.sniffing.base_sniffer import Sniffer
from setezor.database.queries import Queries
from .base_job import BaseJob, CustomScheduler, MessageObserver
import io
import traceback
import asyncio
from setezor.tools.ip_tools import get_ipv4

from setezor.network_structures import IPv4Struct, RouteStruct


class ScapyLogTask(ScapyScanTask):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler: CustomScheduler, name: str, db: Queries, data: str, scapy_logs: str, scanning_ip: str, scanning_mac: str, task_id: int):
        super(ScapyScanTask, self).__init__(agent_id=agent_id, observer=observer, scheduler=scheduler, name=name, update_graph=False)
        self.db = db
        self.task_id = task_id
        self.scanning_ip = scanning_ip
        self.scanning_mac = scanning_mac
        self._coro = self.run(data=data, scanning_ip=scanning_ip, scanning_mac=scanning_mac, scapy_logs=scapy_logs, task_id=task_id)
        
    async def parse_pkt_list(self, data: str, scapy_logs:str):
        sniffer = Sniffer('parse', None, log_path=scapy_logs)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sniffer.read_pcap, io.BytesIO(data))
        await loop.run_in_executor(None, sniffer.save_sniffing_as_pcap, scapy_logs, result)
        return await loop.run_in_executor(None, sniffer.parse_packets, result)
    
    async def run(self, data: str, scanning_ip: str, scanning_mac: str, scapy_logs: str, task_id: int):
        try:
            parsed_pkt_list = await self.parse_pkt_list(data=data, scapy_logs=scapy_logs)
            for pkt in parsed_pkt_list:
                host = IPv4Struct(address=pkt['child_ip'])
                target = IPv4Struct(address=pkt['parent_ip'])
                route = RouteStruct(agent_id=self.agent_id, routes=[host, target])
                self.db.route.create(route=route, task_id=self.task_id)
            self.logger.debug('Parse pcap file and extract information from %s packets', len(parsed_pkt_list))
            self.db.task.set_finished_status(index=task_id)
        except Exception as e:
            self.db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            self.logger.error('Fail with parse pcap-file. Error stacktrace:\n%s', traceback.format_exc())
            raise e