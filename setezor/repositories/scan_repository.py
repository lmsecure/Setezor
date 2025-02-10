from setezor.models import Scan, L4Software, Port, IP, L7, L7Software, Software, Domain, Vendor, MAC, DNS_NS, Vulnerability, L7SoftwareVulnerability, L4SoftwareVulnerability
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy import select, func, text, tuple_ , and_
from sqlalchemy.orm import aliased

class ScanRepository(SQLAlchemyRepository[Scan]):
    model = Scan

    async def l4_comparison_scan_data(self, project_id: str, scan_id: str):

        stmt = select(IP, Port, Software).select_from(Port)\
        .join(IP, Port.ip_id == IP.id)\
        .join(L4Software, L4Software.l4_id == Port.id)\
        .join(Software, Software.id == L4Software.software_id)\
        .filter(Port.scan_id == scan_id,
                Port.project_id == project_id,
                Software.product != None)

        result =  await self._session.exec(stmt)
        return result.all()
    
    async def l7_comparison_scan_data(self, project_id: str, scan_id: str):

        stmt = select(IP, Domain, Port, Software, Vendor).select_from(Port)\
        .join(IP, Port.ip_id == IP.id)\
        .join(L7, L7.port_id == Port.id)\
        .join(Domain, L7.domain_id == Domain.id)\
        .join(L7Software, L7Software.l7_id == L7.id)\
        .join(Software, L7Software.software_id == Software.id)\
        .join(Vendor, Software.vendor_id == Vendor.id)\
        .filter(Port.scan_id == scan_id,
                Port.project_id == project_id,
                Software.product != None)

        result =  await self._session.exec(stmt)
        return result.all()
    
    async def vulnerabilites_comparison_scan_l4_data(self, project_id: str, scan_id: str):

        stmt = select(IP, Port, Vulnerability).select_from(Port)\
        .join(L4Software, L4Software.l4_id == Port.id)\
        .join(L4SoftwareVulnerability, L4SoftwareVulnerability.l4_software_id == L4Software.id)\
        .join(Vulnerability, Vulnerability.id == L4SoftwareVulnerability.vulnerability_id)\
        .join(IP, Port.ip_id == IP.id)\
        .filter(Port.project_id == project_id, Port.scan_id == scan_id)

        result =  await self._session.exec(stmt)
        return result.all()
    
    async def vulnerabilites_comparison_scan_l7_data(self, project_id: str, scan_id: str):

        stmt = select(IP, Port, Domain, Vulnerability).select_from(L7)\
            .join(Port, Port.id == L7.port_id)\
            .join(Domain, Domain.id == L7.domain_id)\
            .join(L7Software, L7Software.l7_id == L7.id)\
            .join(L7SoftwareVulnerability, L7SoftwareVulnerability.l7_software_id == L7Software.id)\
            .join(Vulnerability, Vulnerability.id == L7SoftwareVulnerability.vulnerability_id)\
            .join(IP, Port.ip_id == IP.id)\
            .filter(L7.project_id == project_id, L7.scan_id == scan_id)
        

        result =  await self._session.exec(stmt)
        return result.all()