import datetime
import traceback
import asyncio
from time import time

from setezor.models import Vulnerability as VulnerabilityModel
from setezor.models.d_software import Software
from setezor.models.dns_a import DNS_A
from setezor.models.domain import Domain
from setezor.models.ip import IP
from setezor.models.l7 import L7
from setezor.models.l7_software import L7Software
from setezor.models.l7_software_vulnerability import L7SoftwareVulnerability
from setezor.models.port import Port
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.target import Target
from setezor.modules.acunetix.vulnerability import Vulnerability
from setezor.modules.project_manager.acunetix import AcunetixApi
from setezor.schemas.task import TaskStatus
from setezor.services.data_structure_service import DataStructureService
from setezor.services.task_service import TasksService
from setezor.tasks.base_job import BaseJob
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.modules.osint.dns_info.dns_info import DNS as DNSModule


class AcunetixScanTask(BaseJob):
    def __init__(self, uow: UnitOfWork, 
                 scheduler, name: str, 
                 scan_id:str,
                 acunetix_scan_id:str,
                 agent_id: int,
                 credentials: dict,
                 task_id: int, 
                 project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.scan_id = scan_id
        self.acunetix_scan_id = acunetix_scan_id
        self.uow=uow
        self.credentials = credentials
        self.task_id = task_id
        self.project_id = project_id
        self._coro = self.run()

    async def _task_func(self):
        result_id = ""
        while True:
            result = await Scan.get_by_id(id=self.acunetix_scan_id, credentials=self.credentials)
            status = result["current_session"]["status"]
            if status in ("completed", "aborted", "failed"):
                result_id = result["current_session"]["scan_session_id"]
                scan_vulnerabilities = await Scan.get_vulnerabilities(id=self.acunetix_scan_id,
                                                                      result_id=result_id,
                                                                      credentials=self.credentials)
                vilnerabilities_detail_tasks = [asyncio.create_task(Vulnerability.get_by_id(id=scan_vuln.get(
                    "target_vuln_id"), credentials=self.credentials)) for scan_vuln in scan_vulnerabilities]
                vulnerabilities_detail = await asyncio.gather(*vilnerabilities_detail_tasks)
                if status == "failed":
                    await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.failed, project_id=self.project_id)
                    raise Exception
                break
            await asyncio.sleep(10)

        vulnerabilities = Vulnerability.from_acunetix_response(vulnerabilities_detail)
        result = []
        if not vulnerabilities_detail:
            return result
        target_address = vulnerabilities_detail[0]["affects_url"]
        acunetix_target_id = vulnerabilities_detail[0]["target_id"]
        scheme, addr = target_address.split("://")
        target_address = addr.split("/")[0]
        data = Target.parse_url(url=f"{scheme}://{target_address}")

        if not "port" in data:
            if scheme == "http":
                data |= {"port": 80}
            else:
                data |= {"port": 443}


        if domain := data.get("domain"):
            try:
                responses =  [await DNSModule.resolve_domain(domain=domain, record="A")]
                new_domain, new_ip, dns_a = DNSModule.proceed_records(domain, responses) # может не разрезолвить
                result.append(new_ip)
                result.append(dns_a)
            except:
                new_domain = Domain(domain=domain)
                new_ip = IP()
                new_dns_a = DNS_A(target_ip=new_ip, target_domain=new_domain)
                result.append(new_ip)
                result.append(new_dns_a)
            result.append(new_domain)

        if ip := data.get("ip"):
            new_ip = IP(ip=ip)
            result.append(new_ip)
            new_domain = Domain()
            result.append(new_domain)
        
        new_port = Port(port=data.get("port"), ip=new_ip)
        result.append(new_port)

        new_l7 = L7(port=new_port, domain=new_domain)
        result.append(new_l7)

        new_software = Software()
        result.append(new_software)

        new_l7_software = L7Software(l7=new_l7, software=new_software)
        result.append(new_l7_software)

        scan_result_statistic = await Scan.get_statistics(scan_id=self.acunetix_scan_id, result_id=result_id, credentials=self.credentials)
        end_date = datetime.datetime.fromisoformat(scan_result_statistic["scanning_app"]["wvs"]["end_date"])

        for vuln in vulnerabilities:
            vuln_obj = VulnerabilityModel(created_at_in_acunetix=end_date, **vuln)
            l7_software_vuln = L7SoftwareVulnerability(l7_software=new_l7_software, vulnerability=vuln_obj)
            result.append(vuln_obj)
            result.append(l7_software_vuln)
        return result

    async def _write_result_to_db(self, result):
        service = DataStructureService(uow=self.uow, result=result, project_id=self.project_id, scan_id=self.scan_id)
        await service.make_magic()
        await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.finished, project_id=self.project_id)

    async def run(self):
        try:
            t1 = time()
            result = await self._task_func()
            await self._write_result_to_db(result=result)
        except Exception as e:
            raise e
