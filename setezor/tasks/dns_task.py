import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver
from setezor.modules.osint.dns_info.dns_info import DNS
from setezor.database.queries import Queries

class DNSTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, domain: str, db: Queries):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.domain = domain
        self._coro = self.run(db=db, task_id=task_id, domain=domain)
        
    async def _task_func(self, domain: str):
        return await DNS.query(domain)
    

    async def _write_result_to_db(self, db: Queries, result):
        db.DNS.write_many(domain = self.domain, data=result, to_update = False)

        
    async def run(self, db: Queries, task_id: int,domain:str):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        try:
            t1 = time()
            result = await self._task_func(domain=domain)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            await self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)