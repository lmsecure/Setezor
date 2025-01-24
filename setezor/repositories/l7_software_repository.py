
from sqlalchemy import func
from setezor.models import L7Software, Port, IP, L7, Software, Domain, Vendor, MAC, DNS_NS, Vulnerability, L7SoftwareVulnerability
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import Select

class L7SoftwareRepository(SQLAlchemyRepository[L7Software]):
    model = L7Software


    async def exists(self, L7Software_obj: L7Software):
        if not (L7Software_obj.l7_id and L7Software_obj.software_id):
            return False
        stmt = select(L7Software).filter(L7Software.l7_id == L7Software_obj.l7_id,
                                         L7Software.software_id == L7Software_obj.software_id,
                                         L7Software.project_id == L7Software_obj.project_id)
        result = await self._session.exec(stmt)
        return result.first() 
    
    async def get_ports_software_info(self, project_id: str):
        ports_software: Select = (
            select(
                IP.ip,
                Port.port,
                Port.protocol,
                Port.state,
                Port.service_name,
                Software.product,
                Software.cpe23,
                Software.version,
                func.count(Port.port).label("port_count"),
                func.count(Port.service_name).label("service_name_count")

            )
            .join(Port, IP.id == Port.ip_id)
            .join(L7, Port.id == L7.port_id, isouter=True)
            .join(L7Software, L7.id == L7Software.l7_id, isouter=True)
            .join(Software, L7Software.software_id == Software.id, isouter=True)
            .filter(IP.project_id == project_id)
            .group_by(
                Port.port,
                Port.protocol,
            )
            .order_by(func.count(Port.port).desc())
            .limit(7)
        )
        result = await self._session.exec(ports_software)
        return result.all()
    
    async def get_product_service_name_info(self, project_id: str):
        products_service_name: Select = (
            select(
                IP.ip,
                Port.service_name,
                Software.product,
                func.count(Port.service_name).label("software_product_count")
            )
            .join(Port, IP.id == Port.ip_id)
            .join(L7, Port.id == L7.port_id, isouter=True)
            .join(L7Software, L7.id == L7Software.l7_id, isouter=True)
            .join(Software, L7Software.software_id == Software.id, isouter=True)
            .filter(IP.project_id == project_id, Software.product != None)
            .group_by(
                Port.service_name,
                Software.product,
            )
            .order_by(func.count(Port.service_name).desc())
            .limit(7)
        )
        result = await self._session.exec(products_service_name)
        return result.all()

    async def get_resource_software_tabulator_data(self, project_id: str):
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
                Domain.domain,
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
            )
            .join(Port, IP.id == Port.ip_id)
            .join(L7, Port.id == L7.port_id)
            .join(Domain, Domain.id == L7.domain_id)
            .join(L7Software, L7.id == L7Software.l7_id)
            .join(Software, L7Software.software_id == Software.id)
            .join(Vendor, Software.vendor_id == Vendor.id)
            .filter(IP.project_id == project_id, Software.product != "")
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
                Domain.domain,
                Vendor.name,
            )
            .order_by(func.count(IP.ip).desc())
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()
    
    async def get_soft_vuln_link_data(self, project_id: str):
        row_number_column = func.row_number().over(
            order_by=func.count(Port.port).desc()
        ).label("id")

        tabulator_dashboard_data = (
            select(
                row_number_column,
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
            ).select_from(Port)
            .join(L7, Port.id == L7.port_id)
            .join(L7Software, L7.id == L7Software.l7_id)
            .join(Software, L7Software.software_id == Software.id)
            .join(L7SoftwareVulnerability, L7Software.id == L7SoftwareVulnerability.l7_software_id,)
            .join(Vulnerability, Vulnerability.id == L7SoftwareVulnerability.vulnerability_id,)
            .join(Vendor, Software.vendor_id == Vendor.id)
            .filter(Port.project_id == project_id, Software.product != None)
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
            .order_by(func.count(Vendor.name).desc())
        )

        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()