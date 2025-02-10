import traceback
from time import time
import asyncio
import itertools
from setezor.tasks.base_job import BaseJob
from setezor.modules.osint.sd_search.domain_brute import Domain_brute
from setezor.modules.osint.sd_search.crtsh import CrtSh


class SdFindTask(BaseJob):

    JOB_URL = "sd_find"

    def __init__(self, scheduler, name: str, task_id: int, domain: str, project_id: str, crt_sh: bool, agent_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.domain = domain
        self.crt_sh = crt_sh
        self.agent_id = agent_id
        self._coro = self.run()


    async def _task_func(self) -> list[str]:
        """Запускает брут домена по словарю и поиск субдоменов по crt_sh

        Returns:
            list[str]: Список доменов
        """
        tasks = []
        tasks = [asyncio.create_task(Domain_brute.query(self.domain,"A"))]
        if self.crt_sh:
            tasks.append(asyncio.create_task(CrtSh.crt_sh(self.domain)))
        result = await asyncio.gather(*tasks)
        return list(set(itertools.chain.from_iterable(result)))

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        data = Domain_brute.restruct_result(domains=result)
        return data, b'', ''
