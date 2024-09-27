import traceback
import asyncio
from typing import Literal
from time import time
import json

from .base_job import BaseJob, MessageObserver
from setezor.app_routes.session import notify_client
from setezor.database.queries import Queries
from setezor.tasks.task_status import TaskStatus
from setezor.modules.cve.crawler import CveCrawler
from setezor.modules.cve.parser import CveParser


class Cve(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, log_path: str, cpe: str, list_res_id, source: Literal['vulners', 'nvd'] | None = None):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.list_res_id = list_res_id
        self.log_path = log_path
        self.db = db
        self.cpe = cpe
        self.source = source
        self.task_id = task_id
        self._coro = self.run()

    async def _task_func(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, CveCrawler.run, self.log_path, self.cpe, self.source)
    
    async def _write_result_to_db(self, file_path):
        result = CveParser.parse_vulners_logs(file_path)
        for vuln in result:
            vuln_obj = self.db.vulnerability.get_or_create(**vuln)
            for res_soft_id in self.list_res_id:
                self.db.vuln_res_soft.get_or_create(resource_soft_id=res_soft_id, vulnerability_id=vuln_obj.id)
            
    async def run(self):
        self.db.task.set_pending_status(index=self.task_id)
        try:
            start_time = time()
            file_path = await self._task_func()
            if file_path:
                await self._write_result_to_db(file_path)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - start_time)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            self.db.task.set_failed_status(index=self.task_id, error_message=traceback.format_exc())
            raise e
        self.db.task.set_finished_status(index=self.task_id)

