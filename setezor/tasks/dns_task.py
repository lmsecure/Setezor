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


    async def run(self):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        try:
            t1 = time()
            result = await self._task_func()
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            await self.send_result_to_parent_agent(result=result)
            return result
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e