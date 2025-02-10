import traceback
from time import time
from typing import Any

from setezor.tasks.base_job import BaseJob
from setezor.modules.osint.dns_info.dns_info import DNS as DNSModule

class DNSTask(BaseJob):

    JOB_URL = "dns_task"

    def __init__(self, scheduler, name: str, task_id: int, project_id: str, domain: str, agent_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.project_id = project_id
        self.task_id = task_id
        self.domain = domain
        self.agent_id = agent_id
        self._coro = self.run()

    async def _task_func(self) -> list[Any]:
        return await DNSModule.query(self.domain)

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        return result, b'', ''