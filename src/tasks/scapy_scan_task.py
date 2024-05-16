import asyncio
from time import time

from tasks.base_job import BaseJob, MessageObserver, CustomScheduler
from modules.sniffing.base_sniffer import Sniffer
from tools.ip_tools import get_ipv4
from database.queries import Queries
from network_structures import IPv4Struct, RouteStruct

class ScapyScanTask(BaseJob):
    
    def __init__(self, agent_id: int, observer: MessageObserver, 
                 scheduler: CustomScheduler, name: str, db: Queries, 
                 iface: str, log_path: str, task_id: int):
        super().__init__(agent_id, observer, scheduler, name)
        self.iface = iface
        self.sniffer = Sniffer(iface=iface, log_path=log_path, write_packet_to_db=self.write_packet_to_db)
        self._coro = self.run()
        self.db = db
        self.task_id = task_id
        self.is_stoped = False
        self.__seen = set()

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
            host = pkt['child_ip']
            target = pkt['parent_ip']
            uniq = f'{host}{target}'
            if uniq not in self.__seen:
                host = IPv4Struct(address=host)
                target = IPv4Struct(address=target)
                route = RouteStruct(agent_id=self.agent_id, routes=[host, target])
                self.db.route.create(route=route, task_id=self.task_id)
                self.__seen.add(uniq)
        else:
            self.db.mac.write(mac=pkt.get('child_mac'), agent_id=self.agent_id)
            self.db.mac.write(mac=pkt.get('parent_mac'), agent_id=self.agent_id)

    async def run(self):
        return await self._start_sniffing()