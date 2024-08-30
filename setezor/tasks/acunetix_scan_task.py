import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver
from setezor.modules.osint.dns_info.dns_info import DNS
from setezor.database.queries import Queries
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.vulnerability import Vulnerability


class AcunetixScanTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, target_id: str, credentials: dict,
                 scan_id: str, db: Queries):
        super().__init__(observer=observer, scheduler=scheduler, name=name)
        self.target_id = target_id
        self.scan_id = scan_id
        self.credentials = credentials
        self.task_id = task_id
        self._coro = self.run(db=db)

    async def _task_func(self, db: Queries):
        while True:
            result = await Scan.get_by_id(id=self.scan_id, credentials=self.credentials)
            status = result["current_session"]["status"]
            if status in ("completed","aborted", "failed"):
                result_id = result["current_session"]["scan_session_id"]
                scan_vulnerabilities = await Scan.get_vulnerabilities(id=self.scan_id, result_id=result_id, credentials=self.credentials)
                vilnerabilities_detail_tasks = [asyncio.create_task(Vulnerability.get_by_id(id=scan_vuln.get(
                    "target_vuln_id"), credentials=self.credentials)) for scan_vuln in scan_vulnerabilities]
                vulnerabilities_detail = await asyncio.gather(*vilnerabilities_detail_tasks)
                if status == "failed":
                    db.task.set_failed_status(index=self.task_id, error_message=traceback.format_exc())
                break
            await asyncio.sleep(10)
        vulns_sctructs = Vulnerability.from_acunetix_response(vulnerabilities_detail)
        vulns = [db.vulnerability.get_or_create(to_update = False,**vuln) for vuln in vulns_sctructs]
        resource = db.resource.get_by_acunetix_id(id = self.target_id)
        vulns_res_soft = [{
            "resource_id" : resource.id,
            "software_id" : None,
            "vulnerability_id" : vuln.id
        } for vuln in vulns]
        db.vuln_res_soft.write_many(data = vulns_res_soft,to_update=False)

    async def run(self, db: Queries):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=self.task_id)
        try:
            t1 = time()
            result = await self._task_func(db=db)
            self.logger.debug('Task func "%s" finished after %.2f seconds',
                              self.__class__.__name__, time() - t1)
            # await self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db',
                              self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s',
                              self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(
                index=self.task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=self.task_id)
