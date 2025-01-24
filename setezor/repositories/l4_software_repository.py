
from sqlalchemy import func
from setezor.models import L4Software, Port, IP, Software, Domain, Vendor, MAC, DNS_NS, Vulnerability, L4SoftwareVulnerability
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import Select

class L4SoftwareRepository(SQLAlchemyRepository[L4Software]):
    model = L4Software

    async def exists(self, L4Software_obj: L4Software):
        if not (L4Software_obj.l4_id and L4Software_obj.software_id):
            return False
        stmt = select(L4Software).filter(L4Software_obj.l4_id == L4Software_obj.l4_id,
                                         L4Software_obj.software_id == L4Software_obj.software_id,
                                         L4Software_obj.project_id == L4Software_obj.project_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_l4_software_tabulator_data(self, project_id: str):
        row_number_column = func.row_number().over(
        order_by=func.count(IP.ip).desc()
        ).label("id")

        tabulator_dashboard_data = (
            select(
                row_number_column,
                IP.ip,
                Port.port,
                Port.protocol,
                Port.service_name,
                Vendor.name,
                Software.product,
                Software.type,
                Software.version,
                Software.build,
                Software.patch,
                Software.platform,
                Software.cpe23,
                func.count(Port.port).label("port_count"),
                func.count(Port.service_name).label("service_name_count"),
            ).select_from(Port)
            .join(IP, Port.ip_id == IP.id)
            .outerjoin(L4Software, Port.id == L4Software.l4_id)
            .outerjoin(Software, L4Software.software_id == Software.id)
            .outerjoin(Vendor, Software.vendor_id == Vendor.id)
            .filter(IP.project_id == project_id)
            .group_by(
                Port.port,
                Port.protocol,
                IP.ip,
                Port.state,
                Port.service_name,
                Software.product,
                Software.cpe23,
                Software.version,
                Software.type,
                Software.build,
                Software.patch,
                Software.platform,
                Vendor.name,
            )
            .order_by(func.count(IP.ip).desc())
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()
    
    async def get_soft_vuln_link_data(self, project_id: str):

        tabulator_dashboard_data = (
            select(
                Vendor.name,
                Software.product,
                Software.type,
                Software.version,
                Software.build,
                Software.patch,
                Software.platform,
                Software.cpe23,
                Vulnerability.name.label("vulnerability_name"),
                Vulnerability.cve,
                Vulnerability.cwe,
            ).select_from(L4Software)
            .join(Software, L4Software.software_id == Software.id)
            .join(L4SoftwareVulnerability, L4Software.id == L4SoftwareVulnerability.l4_software_id,)
            .join(Vulnerability, Vulnerability.id == L4SoftwareVulnerability.vulnerability_id,)
            .join(Vendor, Software.vendor_id == Vendor.id)
            .filter(L4Software.project_id == project_id, Software.product != None)
            .group_by(
                Vendor.name,
                Software.product,
                Software.type,
                Software.version,
                Software.build,
                Software.patch,
                Software.platform,
                Software.cpe23,
                Vulnerability.name,
                Vulnerability.cve,
                Vulnerability.cwe,
            )
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()