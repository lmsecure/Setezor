from base64 import b64decode
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.tasks.base_job import BaseJob
from setezor.modules.masscan.parser import BaseMasscanParser



class MasscanLogTask(BaseJob):

    def __init__(self, uow: UnitOfWork, scheduler, name: str, 
                 task_id: int, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: int, filename: str, file: str, interface_ip_id: int, ip: str, mac: str):
        super().__init__(scheduler=scheduler, name=name)
        self.uow: UnitOfWork = uow
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.filename = filename
        self.file = file
        self.interface_ip_id = interface_ip_id
        self.ip = ip
        self.mac = mac
        self._coro = self.run()

    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        ports = await BaseMasscanParser._parser_results(format=self.filename.split('.')[-1], input_data=data)
        result = await BaseMasscanParser.restruct_result(data=ports, agent_id=self.agent_id, interface_ip_id=self.interface_ip_id)
        return result

    @BaseJob.local_task_notifier
    async def run(self):
        return await self._task_func()
