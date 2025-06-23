
from base64 import b64decode
from setezor.tasks.base_job import BaseJob
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.modules.sniffing.scapy_parser import ScapyParser



class ScapyLogsTask(BaseJob):

    def __init__(self, task_manager, scheduler, name: str, task_id: int, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: int, file: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_manager = task_manager
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.file = file
        self._coro = self.run()


    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        return ScapyParser.parse_logs(data = data)

    @BaseJob.local_task_notifier
    async def run(self):
        pkt_list = await self._task_func()
        return await ScapyParser.restruct_result(data=pkt_list, agent_id=self.agent_id)