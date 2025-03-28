

from sqlmodel import func
from setezor.models import L7, IP, Port, Domain, L7Software, L7SoftwareVulnerability, Vulnerability, Software, Vendor
from setezor.models.l7_software_vulnerability_screenshot import L7SoftwareVulnerabilityScreenshot
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select

class L7Repository(SQLAlchemyRepository[L7]):
    model = L7


    async def list(self, project_id: str):
        stmt = select(L7.id, 
                      IP.ip, 
                      Port.port, 
                      Domain.domain,
                      func.count(L7SoftwareVulnerability.id).label("cnt"))\
        .join(Port, L7.port_id == Port.id)\
        .join(Domain, L7.domain_id == Domain.id)\
        .join(IP, Port.ip_id == IP.id)\
        .join(L7Software, L7Software.l7_id == L7.id, isouter=True)\
        .join(L7SoftwareVulnerability, L7SoftwareVulnerability.l7_software_id == L7Software.id, isouter=True)\
        .filter(L7.project_id==project_id)\
        .group_by(L7.id)

        res = await self._session.exec(stmt)
        return res.all()


    async def vulnerabilities(self, project_id:str, l7_id: str):
        stmt = select(L7SoftwareVulnerability.id.label("abc"), 
                      L7SoftwareVulnerability.confirmed.label("confirmed"),
                      Vendor,
                      Software, 
                      Vulnerability)\
        .join(L7SoftwareVulnerability, L7SoftwareVulnerability.vulnerability_id== Vulnerability.id)\
        .join(L7Software, L7Software.id == L7SoftwareVulnerability.l7_software_id)\
        .join(Software, L7Software.software_id == Software.id)\
        .join(L7, L7.id == L7Software.l7_id)\
        .join(Vendor, Vendor.id == Software.vendor_id)\
        .filter(L7.id == l7_id)
        result = await self._session.exec(stmt)
        return result.all()


    async def exists(self, l7_obj: L7):
        port = l7_obj.port.port if l7_obj.port else ""
        domain = l7_obj.domain.domain if l7_obj.domain else ""
        ip_obj = l7_obj.port.ip if l7_obj.port else ""
        ip = ip_obj.ip if ip_obj else ""
        port_id = l7_obj.port_id
        domain_id = l7_obj.domain_id

        if port_id and domain_id:
            stmt = select(L7).join(Port, L7.port_id == port_id).join(Domain, L7.domain_id == domain_id)\
                .filter(L7.project_id == l7_obj.project_id)
        elif port_id:
            stmt = select(L7).join(Port, L7.port_id == port_id).join(Domain, L7.domain_id == Domain.id)\
                .filter(Domain.domain == domain, L7.project_id == l7_obj.project_id)
        elif domain_id:
            stmt = select(L7).join(Domain, L7.domain_id == domain_id).join(Port, L7.port_id == Port.id)\
                .filter(Port.port == port, L7.project_id == l7_obj.project_id)
        else:
            
            stmt = select(L7).join(Domain, L7.domain_id == Domain.id).join(Port, L7.port_id == Port.id)\
                .join(IP, Port.ip_id == IP.id).filter(Port.port == port, 
                                                      Domain.domain == domain, 
                                                      IP.ip == ip,
                                                      L7.project_id == l7_obj.project_id)
        stmt = stmt.filter(L7.scan_id == l7_obj.scan_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_resource_for_snmp(self, project_id: str, scan_id: str):
        stmt = select(IP.ip, Port.port).\
                select_from(Port).\
                    join(IP, IP.id == Port.ip_id).\
                        filter(Port.project_id == project_id, Port.scan_id == scan_id, Port.service_name == "snmp", Port.protocol == "udp") # TODO fixme - Port.protocol == "udp" - это временное решение (нашло порты с tcp)
        result = await self._session.exec(stmt)
        return result.all()