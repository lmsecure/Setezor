import traceback
from time import time

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
            result_data = WhoisModule.restruct_result(target=self.target, result=result)
            await self.send_result_to_parent_agent(result=result_data)
            return result
            # TODO 
            # if not result:
            #     notify
            # self.logger.debug('Task func "%s" finished after %.2f seconds',
            #                   self.__class__.__name__, time() - t1)
            # self._write_result_to_db(db=db, result=result, target=target)
            # self.logger.debug('Result of task "%s" wrote to db',
            #                   self.__class__.__name__)
        # except Exception as e:
        #     self.logger.error('Task "%s" failed with error\n%s',
        #                       self.__class__.__name__, traceback.format_exc())
        #     task.set_failed_status(
        #         index=task_id, error_message=traceback.format_exc())
        #     raise e
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e
        # task.set_finished_status(index=task_id)
