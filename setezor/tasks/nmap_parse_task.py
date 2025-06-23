from base64 import b64decode
from setezor.tasks.base_job import BaseJob
from setezor.modules.nmap.parser import NmapParser



class NmapParseTask(BaseJob):
    def __init__(self, 
                 task_manager, 
                 scheduler, name: str, task_id: str, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: str, 
                 file: str, filename: str, interface_ip_id: str, mac: str, ip: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.task_manager = task_manager
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.file = file
        self.filename = filename
        self.interface_ip_id = interface_ip_id
        self.mac = mac
        self.ip = ip
        self._coro = self.run()

    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        data = NmapParser.parse_xml(data)
        parse_result, traceroute = NmapParser().parse_hosts(scan = data.get('nmaprun'), agent_id=self.agent_id, self_address={'ip': self.ip, 'mac': self.mac})
        result = NmapParser.restruct_result(data=parse_result, interface_ip_id=self.interface_ip_id, traceroute=traceroute)
        return result

    @BaseJob.local_task_notifier
    async def run(self):
        return await self._task_func()
