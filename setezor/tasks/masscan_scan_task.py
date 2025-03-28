import os
import signal
import psutil
from .base_job import BaseJob
from setezor.modules.masscan.executor import MasscanScanner
from setezor.modules.masscan.parser import BaseMasscanParser
from setezor.modules.masscan.executor import MasscanScanner
from setezor.tools.ip_tools import get_ipv4, get_mac


class MasscanScanTask(BaseJob):

    JOB_URL = "masscan_scan_task"
    def __init__(self, scheduler, name: str, task_id: int,  target: str, project_id:str, agent_id: int, ping: bool, ports: str, format: str, wait: int, source_port: int, max_rate: int, search_udp_port: bool, interface_ip_id: int, interface: str):
        super().__init__(scheduler = scheduler, name = name)
        self.interface = interface
        self.interface_ip_id = interface_ip_id
        self.interface_addr = get_ipv4(self.interface)
        self.interface_mac = get_mac(self.interface).upper()
        self.project_id = project_id
        self.agent_id = agent_id
        self.target = target
        self.ping = ping
        self.ports = ports
        self.format = format
        self._wait = wait
        self.task_id = task_id
        self.source_port = source_port
        self.max_rate = max_rate
        self.search_udp_port = search_udp_port
        self.pid = None
        self._coro = self.run()

    async def _task_func(self) -> str:
        if self.ping:
            masscan_obj = MasscanScanner(task=self, 
                                         target=self.target, 
                                         search_udp_port=self.search_udp_port, 
                                         ping=self.ping, 
                                         max_rate=self.max_rate, 
                                         source_port=self.source_port, 
                                         format=self.format, 
                                         wait=self._wait, 
                                         interface_addr=self.interface_addr, 
                                         interface=self.interface)
        else:
            masscan_obj = MasscanScanner(task=self, 
                                         target=self.target, 
                                         ports=self.ports, 
                                         search_udp_port=self.search_udp_port, 
                                         max_rate=self.max_rate, 
                                         source_port=self.source_port, 
                                         format=self.format, 
                                         wait=self._wait, 
                                         interface_addr=self.interface_addr, 
                                         interface=self.interface)
        return await masscan_obj.async_execute(log_path = None)
        
    @BaseJob.remote_task_notifier    
    async def run(self):
        result = await self._task_func()
        if not result:
            raise Exception("Ports not found")
        ports = await BaseMasscanParser._parser_results(format=self.format, input_data=result)
        result_data = await BaseMasscanParser.restruct_result(data=ports, agent_id=self.agent_id, interface_ip_id=self.interface_ip_id)
        return result_data, result.encode(), self.format
    
    async def soft_stop(self):
        for process in psutil.process_iter():
            if process.ppid() == self.pid:
                os.kill(process.pid, signal.SIGKILL)
        os.kill(self.pid, signal.SIGKILL)