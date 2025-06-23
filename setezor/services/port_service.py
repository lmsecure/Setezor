from setezor.schemas.port import PortSchema, PortSchemaAdd
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Vulnerability, L4Software, L4SoftwareVulnerability
from setezor.data_writer.data_structure_service import DataStructureService
from typing import List


class PortService(BaseService):
    async def create(self, port: PortSchemaAdd) -> int:
        port_dict = port.model_dump()
        async with self._uow:
            port_id = self._uow.port.add(port_dict)
            await self._uow.commit()
            return port_id

    async def list(self) -> List[PortSchema]:
        async with self._uow:
            ports = await self._uow.port.list()
            return ports

    async def get(self, id: int) -> PortSchema:
        async with self._uow:
            port = await self._uow.port.find_one(id=id)
            return port
        
    async def get_resources(self, project_id: str) -> List:
        async with self._uow:
            last_scan = await self._uow.scan.last(project_id=project_id)
            resources = await self._uow.port.resource_list(project_id=project_id, scan_id=last_scan.id)
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

    async def add_vulnerability(self, project_id: str, id: int, data:dict):
        result = []
        async with self._uow:
            l4_obj = await self._uow.port.find_one(project_id=project_id, id=id)
            scan_id = l4_obj.scan_id
            software_version_id = data.pop("software_version_id")
            vulnerability = Vulnerability(**data)
            l4_software = L4Software(software_version_id=software_version_id, l4_id=id)
            resource_software_vulnerability = L4SoftwareVulnerability(l4_software=l4_software, 
                                                                      vulnerability=vulnerability,
                                                                      confirmed=True)
            result.extend([vulnerability, l4_software, resource_software_vulnerability])
        service = DataStructureService(uow=self._uow)
        await service.make_magic(result=result, project_id=project_id, scan_id=scan_id)
        return True

    async def list_vulnerabilities(self, l4_id: str, project_id: str) -> List:
        async with self._uow:
            resource_vulnerabilities = await self._uow.port.vulnerabilities(l4_id=l4_id, project_id=project_id)
            links_objs = await self._uow.vulnerability_link.all_on_l4(project_id=project_id, l4_id=l4_id)
            count_scr = await self._uow.l4_software_vulnerability_screenshot.count_on_l4(project_id=project_id, l4_id=l4_id)
        links = {}
        for vuln_id, link in links_objs:
            if (item := links.get(vuln_id)):
                item.append(link)
            else:
                links[vuln_id] = [link]
        count_scr = dict(count_scr)
        result = []
        for l4_soft_vulnid, confirmed, vendor, software_version, software, software_type, vuln in resource_vulnerabilities:
            result.append(
                {
                    "vuln_res_soft_id": l4_soft_vulnid,
                    "confirmed": confirmed,
                    "vendor": vendor.name,
                    "product": software.product,
                    "type": software_type.name,
                    "version": software_version.version,
                    "build": software_version.build,
                    "links": links.get(vuln.id, []),
                    "screenshots_count": count_scr.get(vuln.id, 0),
                    **vuln.model_dump(exclude=["response"])
                }
            )
        return result

    async def get_resources_for_snmp(self, project_id: str, scan_id):
        async with self._uow:
            data = await self._uow.port.get_resource_for_snmp(project_id=project_id, scan_id=scan_id)
        return [{"ip" : ip, "port" : port} for ip, port in data]