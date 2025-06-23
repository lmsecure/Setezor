from setezor.services.project_service import ProjectService
from setezor.services.software import SoftwareService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from .base_job import BaseJob
from setezor.models import Vulnerability, \
    L4SoftwareVulnerability, \
    VulnerabilityLink

from setezor.modules.search_vulns.search_vulns import SearchVulns

class CVERefresher(BaseJob):
    def __init__(self, task_manager,
                 scheduler, 
                 name: str, 
                 task_id: str, 
                 project_id: str, 
                 scan_id: str,
                 project_service: ProjectService,
                 software_service: SoftwareService, 
                 agent_id: int):
        super().__init__(scheduler=scheduler, name=name)
        self.task_manager = task_manager
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.vulnerabilities = {}
        self.links = set()
        self.results = {}
        self.project_service = project_service
        self.software_service = software_service
        self._coro = self.run()

    async def get_vulnerabilities(self, dataset, token: str, model, key: str):
        vulnerabilities = []    
        for vendor_name, lx_soft, soft_version, software in dataset:   
            cpe23 = soft_version.cpe23.split(", ")[0] if soft_version.cpe23 else ""
            if not cpe23:
                cpe23 = f"cpe:2.3:a:{vendor_name}:{software.product}:{soft_version.version}:*:*:*:*:*:*:*"
                
            if cpe23 in self.results:
                result = self.results.get(cpe23)
            else:
                result = await SearchVulns.find(token=token, query_string=cpe23)
                self.results[cpe23] = result
                for k in result.keys():
                    if not result[k]["vulns"]:
                        pot_cpes = result[k]["pot_cpes"]
                        if not pot_cpes:
                            result = {}
                            break
                        pot_cpes = sorted(pot_cpes, key=lambda x: x[1])
                        result = await SearchVulns.find(token=token, query_string=pot_cpes[-1][0])
                        self.results[cpe23] = result
            result_vulns = []
            for k in result.keys():
                data = result.get(k, [])
                vulns = data.get("vulns")
                for cve in vulns.keys():
                    if "CVE" in cve:
                        result_vulns.append((cve, vulns[cve]))
            for cve, data in result_vulns:
                if cve in self.vulnerabilities:
                    vuln = self.vulnerabilities[cve]
                else:
                    vuln = Vulnerability(name=cve, cve=cve, description=data["description"])
                    self.vulnerabilities[cve] = vuln
                    if data["cvss_ver"]:
                        setattr(vuln, f"cvss{data["cvss_ver"][0]}_score", float(data.get("cvss")))
                        setattr(vuln, f"cvss{data["cvss_ver"][0]}", data.get("cvss_vec"))
                    vulnerabilities.append(vuln)
                
                
                new_soft_vuln = model(vulnerability=vuln)
                setattr(new_soft_vuln, key, lx_soft.id)
                vulnerabilities.append(new_soft_vuln)
                for link in data.get("exploits", []):
                    if not f"{cve}_{link}" in self.links:
                        link_obj = VulnerabilityLink(link=link, vulnerability=vuln)
                        vulnerabilities.append(link_obj)
                        self.links.add(f"{cve}_{link}")
        return vulnerabilities
    
    async def _task_func(self):
        token = ""
        project = await self.project_service.get_by_id(project_id=self.project_id)
        token = project.search_vulns_token
        if not token:
            return
        new_vulnerabilities = []
        l4_soft_with_cpe23 = await self.software_service.for_search_vulns(project_id=self.project_id,
                                                                    scan_id=self.scan_id)

        l4_software_vulnerabilities = await self.get_vulnerabilities(l4_soft_with_cpe23, 
                                                                     token, 
                                                                     L4SoftwareVulnerability,
                                                                     "l4_software_id")
        new_vulnerabilities.extend(l4_software_vulnerabilities)
        return new_vulnerabilities

    @BaseJob.local_task_notifier
    async def run(self):
        return await self._task_func()
