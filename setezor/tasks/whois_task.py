import traceback
from time import time
import orjson
from .base_job import BaseJob
from setezor.modules.osint.whois.whoistest import Whois as WhoisModule

class WhoisTask(BaseJob):

    JOB_URL = "whois_task"

    def __init__(self, scheduler, name: str, task_id: int, target: str, agent_id: int, project_id: str):
        super().__init__(scheduler = scheduler, name = name)
        self.task_id = task_id
        self.target = target
        self.project_id = project_id
        self.agent_id = agent_id
        self._coro = self.run()
        

    async def _task_func(self):
        return WhoisModule.get_whois(ip=self.target)


    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        result_data = WhoisModule.restruct_result(target=self.target, result=result)
        return result_data, orjson.dumps(result), 'json'
