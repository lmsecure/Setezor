import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from setezor.network_structures import SoftwareStruct
from setezor.modules.wappalyzer.wappalyzer import WappalyzerParser


class Wappalyzer(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, data: dict, groups: list):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.data = data
        self.groups = groups
        self._coro = self.run(db=db, task_id=task_id)


    async def _task_func(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(WappalyzerParser.parse_json(self.data, self.groups))


    async def _write_result_to_db(self, db: Queries, result: dict):
        if result:
            for software in result.get('softwares'):
                tmp = {'port' : result.get('port')}
                if 'ip' in result:
                    tmp.update({'ip': result.get('ip')})
                if 'domain' in result:
                    tmp.update({'domain': result.get('domain')})
                tmp.update(software.model_dump())
                db.resource_software.get_or_create(**tmp)


    async def run(self, db: Queries, task_id: int):
        db.task.set_pending_status(index=task_id)
        try:
            start_time = time()
            result = await self._task_func()
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - start_time)
            await self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
