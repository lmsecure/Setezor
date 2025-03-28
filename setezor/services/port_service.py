from setezor.schemas.port import PortSchema, PortSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Vulnerability, L4Software, L4SoftwareVulnerability
from setezor.services import DataStructureService
from typing import List


class PortService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, port: PortSchemaAdd) -> int:
        port_dict = port.model_dump()
        async with uow:
            port_id = uow.port.add(port_dict)
            await uow.commit()
            return port_id

    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[PortSchema]:
        async with uow:
            ports = await uow.port.list()
            return ports

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> PortSchema:
        async with uow:
            port = await uow.port.find_one(id=id)
            return port

    @classmethod
    async def get_resources(cls, uow: UnitOfWork, project_id: str) -> List:
        async with uow:
            resources = await uow.port.resource_list(project_id=project_id)
        result = []
        for res in resources:
            result.append({
                "id": res.id,
                "ip": res.ip,
                "port": res.port,
                "vuln_count": res.cnt
                })
        return result

    @classmethod
    async def add_vulnerability(cls, uow: UnitOfWork, project_id: str, id: int, data:dict):
        result = []
        async with uow:
            l4_obj = await uow.port.find_one(project_id=project_id, id=id)
            scan_id = l4_obj.scan_id
            software_id = data.pop("software_id")
            vulnerability = Vulnerability(**data)
            l4_software = L4Software(software_id=software_id, l4_id=id)
            resource_software_vulnerability = L4SoftwareVulnerability(l4_software=l4_software, 
                                                                      vulnerability=vulnerability,
                                                                      confirmed=True)
            result.extend([vulnerability, l4_software, resource_software_vulnerability])
        service = DataStructureService(uow=uow, result=result, project_id=project_id, scan_id=scan_id)
        await service.make_magic()
        return True

    @classmethod
    async def list_vulnerabilities(cls, uow: UnitOfWork, l4_id: str, project_id: str) -> List:
        async with uow:
            resource_vulnerabilities = await uow.port.vulnerabilities(l4_id=l4_id, project_id=project_id)
            links_objs = await uow.vulnerability_link.all_on_l4(project_id=project_id, l4_id=l4_id)
            count_scr = await uow.screenshots.count_on_l4(project_id=project_id, l4_id=l4_id)
        links = {}
        for vuln_id, link in links_objs:
            if (item := links.get(vuln_id)):
                item.append(link)
            else:
                links[vuln_id] = [link]
        count_scr = dict(count_scr)
        result = []
        for l4_soft_vulnid, confirmed, vendor, software, vuln in resource_vulnerabilities:
            result.append(
                {
                    "vuln_res_soft_id": l4_soft_vulnid,
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