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


    async def run(self):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. ...
        3. Вернуть результат родительскому агенту
        """
        try:
            t1 = time()
            result = await self._task_func()
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            data = Domain_brute.restruct_result(domains=result)
            await self.send_result_to_parent_agent(result=data)
            return result
        except Exception as e:
            print('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            raise e
