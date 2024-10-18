import asyncio
from time import time
import traceback

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from ipaddress import IPv4Address

from setezor.modules.snmp.snmp import SNMP


class  SNMP_crawler_task(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, ip: str, community_string: str):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.task_id = task_id
        self.db = db

        self.ip = ip
        self.community_string = community_string

        self._coro = self.run()


    async def _task_func(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(SNMP.walk(ip_address=self.ip, community_string=self.community_string))


    async def _write_result_to_db(self, data):
        print('\n', "_write_result_to_db from SNMP_crawler:")
        for item in data:
            print(item)


    async def run(self):
        self.db.task.set_pending_status(index=self.task_id)
        try:
            IPv4Address(self.ip)
            if not self.community_string:
                raise Exception("Community string must not be empty")
            start_time = time()
            result = await self._task_func()
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - start_time)
            await self._write_result_to_db(data=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            self.db.task.set_failed_status(index=self.task_id, error_message=traceback.format_exc())
            raise e
        self.db.task.set_finished_status(index=self.task_id)