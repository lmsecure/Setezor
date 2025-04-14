import asyncio
import datetime
from time import time
from setezor.models import Vulnerability as VulnerabilityModel, \
    Software, \
    Domain, IP, Port, DNS_A
from setezor.models.l4_software import L4Software
from setezor.models.l4_software_vulnerability import L4SoftwareVulnerability
from setezor.modules.acunetix.scan import Scan
from setezor.modules.acunetix.target import Target
from setezor.modules.acunetix.vulnerability import Vulnerability
from setezor.schemas.task import TaskStatus
from setezor.services.task_service import TasksService
from setezor.tasks.base_job import BaseJob
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.modules.osint.dns_info.dns_info import DNS as DNSModule
from setezor.tools.url_parser import parse_url

class AcunetixScanTask(BaseJob):
    def __init__(self, uow: UnitOfWork, 
                 scheduler, name: str, 
                 target_address: str,
                 scan_id:str,
                 acunetix_scan_id:str,
                 agent_id: int,
                 credentials: dict,
                 task_id: int, 
                 project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.target_address = target_address
        self.acunetix_scan_id = acunetix_scan_id
        self.scan_id = scan_id
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
                    await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.failed)
                    raise Exception
                break
            await asyncio.sleep(10)
        if not vulnerabilities_detail:
            return
        vulns_sctructs = Vulnerability.from_acunetix_response(vulnerabilities_detail)
        result = []
        data = parse_url(url=self.target_address)
        if domain := data.get("domain"):
            try:
                responses =  [await DNSModule.resolve_domain(domain=domain, record="A")]
                new_domain, new_ip, *new_dns_a = DNSModule.proceed_records(domain, responses) # может не разрезолвить
                result.append(new_ip)
                result.extend(new_dns_a)
            except:
                new_domain = Domain(domain=domain)
                new_ip = IP()
                new_dns_a = [DNS_A(target_ip=new_ip, target_domain=new_domain)]
                result.append(new_ip)
                result.extend(new_dns_a)
            result.append(new_domain)

        if ip := data.get("ip"):
            new_ip = IP(ip=ip)
            result.append(new_ip)
            new_domain = Domain()
            result.append(new_domain)
            new_dns_a = DNS_A(target_ip=new_ip, target_domain=new_domain)
            result.append(new_dns_a)

        new_port = Port(port=data.get("port"), ip=new_ip)
        result.append(new_port)

        new_software = Software()
        result.append(new_software)

        new_l4_software = L4Software(l4=new_port, dns_a=new_dns_a, software=new_software)
        result.append(new_l4_software)        

        scan_result_statistic = await Scan.get_statistics(scan_id=self.acunetix_scan_id, result_id=result_id, credentials=self.credentials)
        end_date = datetime.datetime.fromisoformat(scan_result_statistic["scanning_app"]["wvs"]["end_date"])

        for vuln in vulns_sctructs:
            vuln_obj = VulnerabilityModel(created_at_in_acunetix=end_date, **vuln)
            l4_software_vuln = L4SoftwareVulnerability(l4_software=new_l4_software, vulnerability=vuln_obj)
            result.append(vuln_obj)
            result.append(l4_software_vuln)
        return result


    @BaseJob.local_task_notifier
    async def run(self):
        return await self._task_func()
