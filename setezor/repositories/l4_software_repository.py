
from sqlalchemy import case, func, literal, text
from setezor.models import L4Software, Port, IP, Software, Vendor, Vulnerability, L4SoftwareVulnerability, DNS_A, Domain, VulnerabilityLink
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, cast, String

class L4SoftwareRepository(SQLAlchemyRepository[L4Software]):
    model = L4Software

    async def exists(self, L4Software_obj: L4Software):
        if not (L4Software_obj.l4_id and L4Software_obj.software_id):
            return False
        stmt = select(L4Software).filter(L4Software.l4_id == L4Software_obj.l4_id,
                                         L4Software.software_id == L4Software_obj.software_id,
                                         L4Software.scan_id == L4Software_obj.scan_id,
                                         L4Software.project_id == L4Software_obj.project_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_l4_software_tabulator_data(self, project_id: str, last_scan_id: str):
        row_number_column = func.row_number().over(
        order_by=func.count(IP.ip).desc()
        ).label("id")

        tabulator_dashboard_data = (
            select(
                row_number_column,
                IP.ip,
                Domain.domain,
                Port.port,
                Port.protocol,
                Port.state,
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
            .join(DNS_A, DNS_A.target_ip_id == IP.id)
            .join(Domain, Domain.id == DNS_A.target_domain_id, isouter=True)
            .join(L4Software, Port.id == L4Software.l4_id, isouter=True)
            .join(Software, L4Software.software_id == Software.id, isouter=True)
            .join(Vendor, Software.vendor_id == Vendor.id, isouter=True)
            .filter(IP.project_id == project_id, IP.scan_id == last_scan_id)
            .group_by(
                Port.port,
                Port.protocol,
                IP.ip,
                Port.state,
                Domain.domain,
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

    async def get_soft_vuln_link_data(self, project_id: str, last_scan_id: str):
        stmt = select(Vendor.name, Software.product, Software.type,
                      Software.version, Software.build, Software.patch,
                      Software.platform, Software.cpe23, 
                      Vulnerability.name.label("vulnerability_name"), Vulnerability.cve, Vulnerability.cwe, VulnerabilityLink.link).select_from(VulnerabilityLink)\
                .join(Vulnerability, Vulnerability.id == VulnerabilityLink.vulnerability_id)\
                .join(L4SoftwareVulnerability, L4SoftwareVulnerability.vulnerability_id == Vulnerability.id)\
                .join(L4Software, L4Software.id == L4SoftwareVulnerability.l4_software_id)\
                .join(Software, Software.id == L4Software.software_id)\
                .join(Vendor, Vendor.id == Software.vendor_id)
        result = await self._session.exec(stmt)
        return result.all()

    async def get_ports_and_protocols(self, project_id: str, last_scan_id: str):
        stmt = select(
            case(
                (Port.protocol.is_(None), "unknown"),
                (Port.protocol == "", "unknown"),
                else_=Port.protocol).label("labels"),
            literal("").label("parents"),
            func.count(Port.protocol).label("graph_values")).filter(Port.project_id == project_id, Port.scan_id == last_scan_id).group_by(Port.protocol)\
        .union(
            select(
                cast(Port.port.label("labels"), String),
                case(
                    (Port.protocol.is_(None), "unknown"),
                    (Port.protocol == "", "unknown"),
                    else_=Port.protocol).label("parents"),
                func.count(Port.port).label("graph_values")).filter(Port.project_id == project_id, Port.scan_id == last_scan_id).group_by(Port.port, Port.protocol)
        )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_product_service_name_info_from_sunburts(self, project_id: str, last_scan_id: str):
        stmt1 = select(
                case(
                    (Port.service_name.is_(None), "unknown"),
                    (Port.service_name == "", "unknown"),
                    else_=Port.service_name).label("labels"),
                literal("").label("parent"),
                func.count(Port.service_name).label("value"))\
            .join(L4Software, L4Software.l4_id == Port.id)\
            .join(Software, Software.id == L4Software.software_id)\
            .filter(Port.project_id == project_id, Port.scan_id == last_scan_id)\
            .group_by(Port.service_name)

        stmt2 = select(
                Software.product.label("labels"),
                case(
                    (Port.service_name.is_(None), "unknown"),
                    (Port.service_name == "", "unknown"),
                    else_=Port.service_name).label("parent"),
                func.count(Software.product).label("value"))\
            .join(L4Software, L4Software.l4_id == Port.id)\
            .join(Software, Software.id == L4Software.software_id)\
            .filter(Port.project_id == project_id, Port.scan_id == last_scan_id)\
            .group_by(Software.product, Port.service_name)

        stmt = stmt1.union(stmt2)
        stmt = select(text("labels"), text("parent"), func.sum(text("value")).label("value"))\
            .select_from(stmt).group_by(text("labels"), text("parent"))
        result = await self._session.exec(stmt)
        return result.all()