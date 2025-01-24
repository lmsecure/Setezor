import json
import traceback
import asyncio
from time import time

from setezor.managers.websocket_manager import WS_MANAGER
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.services.data_structure_service import DataStructureService
from setezor.services.task_service import TasksService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from cpeguess.cpeguess import CPEGuess

from .base_job import BaseJob
from setezor.models import Vulnerability, \
    L4SoftwareVulnerability, \
    L7SoftwareVulnerability, \
    VulnerabilityLink

from setezor.modules.search_vulns.search_vulns import SearchVulns
from setezor.modules.acunetix.schemes.vulnerability import Vulnerability as VulnerabilityScheme


class CVERefresher(BaseJob):
    def __init__(self, uow: UnitOfWork, 
                 scheduler, 
                 name: str, 
                 task_id: str, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: int):
        super().__init__(scheduler=scheduler, name=name)
        self.uow: UnitOfWork = uow
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.vulnerabilities = {}
        self.links = set()
        self.results = {}
        self._coro = self.run()

    async def get_vulnerabilities(self, dataset, token: str, model, key: str):
        vulnerabilities = []    
        for vendor_name, lx_soft, software in dataset:   
            cpe23 = software.cpe23.split(", ")[0] if software.cpe23 else ""
            if not cpe23:
                cpe23 = f"cpe:2.3:a:{vendor_name}:{software.product}:{software.version}:*:*:*:*:*:*:*"
                
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
                        setattr(vuln, f"cvss{data["cvss_ver"][0]}_score", data.get("cvss"))
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
        async with self.uow as uow:
            project = await uow.project.find_one(id=self.project_id)
            token = project.search_vulns_token
        if not token:
            message = WebSocketMessage(title="Warning", text=f"No token provided", type="warning")
            await WS_MANAGER.send_message(project_id=self.project_id, message=message) 
            return []
        new_vulnerabilities = []
        async with self.uow as uow:
            l4_soft_with_cpe23, l7_soft_with_cpe23 = await uow.software.for_search_vulns(project_id=self.project_id, 
                                                                                         scan_id=self.scan_id)
        
        l4_software_vulnerabilities = await self.get_vulnerabilities(l4_soft_with_cpe23, 
                                                                     token, 
                                                                     L4SoftwareVulnerability,
                                                                     "l4_software_id")
        l7_software_vulnerabilities = await self.get_vulnerabilities(l7_soft_with_cpe23, 
                                                                     token, 
                                                                     L7SoftwareVulnerability,
                                                                     "l7_software_id")
        new_vulnerabilities.extend(l4_software_vulnerabilities)
        new_vulnerabilities.extend(l7_software_vulnerabilities)
        return new_vulnerabilities

    async def _write_result_to_db(self, result):
        service = DataStructureService(uow=self.uow, 
                                       result=result, 
                                       project_id=self.project_id, 
                                       scan_id=self.scan_id)
        await service.make_magic()
        await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.finished, project_id=self.project_id)

    async def run(self):
        try:
            t1 = time()
            result = await self._task_func()
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            await self._write_result_to_db(result=result)
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e
