from tasks.base_job import BaseJob, MessageObserver, CustomScheduler
from modules.sniffing.base_sniffer import Sniffer
from tools.ip_tools import get_self_ip
from database.queries import Queries
import asyncio
from time import time


class ScapyScanTask(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler: CustomScheduler, name: str, db: Queries, iface: str, log_path: str, task_id: int):
        super().__init__(observer, scheduler, name)
        self.iface = iface
        self.sniffer = Sniffer(iface=iface, log_path=log_path, write_packet_to_db=self.write_packet_to_db)
        self._coro = self.run()
        self.db = db
        self.task_id = task_id
        self.is_stoped = False

    async def _start_sniffing(self):
        self.sniffer.start_sniffing()
        self.logger.debug('Scapy scan task started')
        self.t1 = time()
        while self.sniffer.sniffer.running:
            await asyncio.sleep(2)
            if self.is_stoped:
                return
            if not self.sniffer.sniffer.thread.is_alive():
                raise Exception('Sniffing was failed. Maybe you dont have permission?')
        
    async def soft_stop(self):
        self.is_stoped = True
        self.sniffer.stop_sniffing()
        self.logger.debug('Scapy scan task stopped')
        self.db.task.set_finished_status(index=self.task_id)
        self.logger.debug('Finish scapy task with name "%s" after %.2f seconds', self.name, time() - self.t1)

    def write_packet_to_db(self, pkt: dict):
        if any(['ip' in j for j in list(pkt.keys())]):
            self.db.l3link.write(start_ip=get_self_ip(self.iface).get('ip'), **pkt)
        else:
            self.db.mac.write(mac=pkt.get('child_mac'))
            self.db.mac.write(mac=pkt.get('parent_mac'))

    async def run(self):
        return await self._start_sniffing()