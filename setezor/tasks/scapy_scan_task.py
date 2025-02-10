import asyncio
from time import time

from setezor.tasks.base_job import BaseJob
from setezor.modules.sniffing.scapy_sniffer import ScapySniffer
from setezor.modules.sniffing.scapy_parser import ScapyParser



class ScapySniffTask(BaseJob):

    JOB_URL = "scapy_sniff_task"
    
    def __init__(self, scheduler, iface: str, agent_id: int, task_id: int, name: str, project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.agent_id = agent_id
        self.project_id = project_id
        self.iface = iface
        self.task_id = task_id
        self.is_stoped = False
        self.sniffer = ScapySniffer(iface=iface)
        self._coro = self.run()


    async def soft_stop(self):
        self.is_stoped = True
        
    def get_result(self):
        logs = self.sniffer.stop_sniffing()
        result = ScapyParser.parse_logs(data=logs)
        result = ScapyParser.restruct_result(data=result, agent_id=self.agent_id)
        return result, logs, "pcap"
    
    @BaseJob.remote_task_notifier
    async def run(self):
        self.sniffer.start_sniffing()
        self.t1 = time()
        while self.sniffer.sniffer.running:
            await asyncio.sleep(2)
            if self.is_stoped:
                return self.get_result()
            if not self.sniffer.sniffer.thread.is_alive():
                raise Exception('Sniffing was failed. Maybe you dont have permission?')