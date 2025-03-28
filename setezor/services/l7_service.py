
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Vulnerability, L7Software, L7SoftwareVulnerability
from setezor.services import DataStructureService
from typing import List, Dict


class L7Service(IService):
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str) -> List[Dict]:
        async with uow:
            resources = await uow.l7.list(project_id=project_id)
        result = []
        for res in resources:
            result.append({
                "id": res.id,
                "ip": res.ip,
                "port": res.port,
                "domain": res.domain,
                "vuln_count": res.cnt
            })
        return result
    
    @classmethod
    async def add_vulnerability(cls, uow: UnitOfWork, project_id: str, id: int, data:dict):
        result = []
        async with uow:
            l7_obj = await uow.l7.find_one(project_id=project_id, id=id)
            scan_id = l7_obj.scan_id
            software_id = data.pop("software_id")
            vulnerability = Vulnerability(**data)
            l7_software = L7Software(software_id=software_id, l7_id=id)
            resource_software_vulnerability = L7SoftwareVulnerability(l7_software=l7_software, 
                                                                      vulnerability=vulnerability,
                                                                      confirmed=True)
            result.extend([vulnerability, l7_software, resource_software_vulnerability])
        service = DataStructureService(uow=uow, result=result, project_id=project_id, scan_id=scan_id)
        await service.make_magic()
        return True


    @classmethod
    async def list_vulnerabilities(cls, uow: UnitOfWork, project_id: str, l7_id: int):
        async with uow:
            resource_vulnerabilities = await uow.l7.vulnerabilities(project_id=project_id, l7_id=l7_id)
            links_objs = await uow.vulnerability_link.all_on_l7(project_id=project_id, l7_id=l7_id)
            count_scr = await uow.screenshots.count_on_l7(project_id=project_id, l7_id=l7_id)
        links = {}
        for vuln_id, link in links_objs:
            if (item := links.get(vuln_id)):
                item.append(link)
            else:
                links[vuln_id] = [link]
        count_scr = dict(count_scr)
        result = []
        for l7_soft_vulnid, confirmed, vendor, software, vuln in resource_vulnerabilities:
            result.append(
                {
                    "vuln_res_soft_id": l7_soft_vulnid,
                    "confirmed": confirmed,
                    "vendor": vendor.name,
                    "product": software.product,
                    "type": software.type,
                    "version": software.version,
                    "build": software.build,
                    "patch": software.patch,
                    "platform": software.platform,
                    "links": links.get(vuln.id, []),
                    "screenshots_count": count_scr.get(vuln.id, 0),
                    **vuln.model_dump(exclude=["response"])
                }
            )
        return result


    @classmethod
    async def get_resources_for_snmp(cls, uow: UnitOfWork, project_id: str, scan_id):
        async with uow:
            data = await uow.l7.get_resource_for_snmp(project_id=project_id, scan_id=scan_id)
        return [{"ip" : ip, "port" : port} for ip, port in data]
