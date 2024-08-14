import traceback
import asyncio
from time import time
import socket
from .base_job import BaseJob, MessageObserver
from setezor.modules.osint.sd_search.domain_brute import Domain_brute
from setezor.modules.osint.sd_search.crtsh import CrtSh
from setezor.database.queries import Queries
from typing import List
import itertools

class SdFindTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, domain: str,crtshtumb:bool, db: Queries):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.domain = domain
        self._coro = self.run(db=db, task_id=task_id, domain=domain, crtshtumb=crtshtumb)
        
    
    async def _task_func(self, domain:str, crtshtumb:bool) -> List[str]:
        """Запускает брут домена по словарю и поиск субдоменов по crtsh

        Args:
            command (str): параметры сканирования

        Returns:
            _type_: Список доменов
        """
        tasks = []
        tasks = [asyncio.create_task(Domain_brute.query(domain,"A"))]
        if crtshtumb:
            tasks.append(asyncio.create_task(CrtSh.crt_sh(domain)))
        result = await asyncio.gather(*tasks)
        return list(set(itertools.chain.from_iterable(result)))
    
    async def _write_result_to_db(self, db: Queries, result) -> None:
        """Метод парсинга результатов и занесения в базу

        Args:
            db (Queries): объект запросов в базу
            result (list): результат
         
        """
        datalist=[]
        for domain_name in result:
            datalist.append({'domain': domain_name, 
                             'is_wildcard': False,})
        db.domain.write_many(data=datalist)
        


        
    async def run(self, db: Queries, task_id: int, domain: str, crtshtumb:bool):
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
            result = await self._task_func(domain=domain,crtshtumb=crtshtumb)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            await self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
        