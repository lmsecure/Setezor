import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from setezor.database.models import Software, Vulnerability, Vulnerability_Resource_Soft
from setezor.modules.search_vulns.search_vulns import SearchVulns
from setezor.modules.acunetix.schemes.vulnerability import Vulnerability as VulnerabilityScheme
from setezor.database.models import Software


class CVERefresher(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, 
                 cpe23: str,res_softs_ids:list[int], token: str, db: Queries):
        super().__init__(observer=observer, scheduler=scheduler, name=name)
        self.db = db
        self.token = token
        self.cpe23 = cpe23
        self.res_softs_ids = res_softs_ids
        self._coro = self.run(db=db, task_id=task_id)

    async def _task_func(self):
        cpe23 = self.cpe23.split(", ")[0]
        result = await SearchVulns.find(token=self.token, query_string=cpe23)
        for k in result.keys():
            if not result[k]["vulns"]:
                pot_cpes = result[k]["pot_cpes"]
                if not pot_cpes:
                    result = {}
                    break
                pot_cpes = sorted(pot_cpes, key=lambda x: x[1])
                result = await SearchVulns.find(token=self.token, query_string=pot_cpes[-1][0])
        result_vulns = []
        for k in result.keys():
            data = result.get(k, [])
            vulns = data.get("vulns")
            for cve in vulns.keys():
                if "CVE" in cve:
                    result_vulns.append((cve, vulns[cve]))

        vulnerabilities = []
        for cve, data in result_vulns:
            vuln = VulnerabilityScheme(
                cve=cve, description=data["description"])
            vuln = self.db.vulnerability.get_or_create(**vuln.model_dump())
            vulnerabilities.append(vuln.id)
            for link in data.get("exploits", []):
                link_obj = {
                    "link": link,
                    "vulnerability_id": vuln.id
                }
                self.db.vulnerability_link.get_or_create(**link_obj)
        for id in vulnerabilities:
            for res_soft_id in self.res_softs_ids:
                vuln_res_soft = {
                    "resource_soft_id": res_soft_id,
                    "vulnerability_id": id
                }
            self.db.vuln_res_soft.get_or_create(**vuln_res_soft)

    async def run(self, db: Queries, task_id: int):
        db.task.set_pending_status(index=task_id)
        try:
            start_time = time()
            result = await self._task_func()
            self.logger.debug('Task func "%s" finished after %.2f seconds',
                              self.__class__.__name__, time() - start_time)
            self.logger.debug('Result of task "%s" wrote to db',
                              self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s',
                              self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(
                index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
