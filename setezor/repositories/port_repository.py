

from sqlalchemy import Select, case, desc
from setezor.models import Port, IP, L4Software, L4SoftwareVulnerability, Vulnerability, Software, Vendor, DNS_A, Domain
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select, func

class PortRepository(SQLAlchemyRepository[Port]):
    model = Port

    async def exists(self, port_obj: Port):
        port = port_obj.port
        ip = port_obj.ip
        ip_id = port_obj.ip_id
        if ip_id:
            stmt = select(Port).join(IP, Port.ip_id == IP.id).filter(Port.port == port,
                                                                     IP.id == ip_id,
                                                                     Port.project_id == port_obj.project_id,
                                                                     Port.scan_id == port_obj.scan_id
                                                                     )
        else:
            stmt = select(Port).join(IP, Port.ip_id == IP.id).filter(Port.port == port, 
                                                                     IP.ip == ip.ip, 
                                                                     Port.project_id == port_obj.project_id,
                                                                     Port.scan_id == port_obj.scan_id
                                                                     )
        result = await self._session.exec(stmt)
        return result.first()


    async def get_node_info(self, ip_id: str, project_id: str):
        stmt = select(Port, Software).select_from(Port)\
            .join(L4Software, L4Software.l4_id == Port.id, isouter=True)\
            .join(Software, L4Software.software_id == Software.id, isouter=True)\
            .filter(Port.ip_id == ip_id, Port.project_id == project_id)
        result = await self._session.exec(stmt)
        return result.all()


    async def get_port_count(self, project_id: str, last_scan_id: str):
        """Считает количество сток"""
        port_count: Select = select(func.count()).select_from(self.model).filter(self.model.project_id == project_id, self.model.scan_id == last_scan_id)
        result = await self._session.exec(port_count)
        port_count_result = result.one()
        return port_count_result


    async def get_top_ports(self, project_id: str, last_scan_id: str):
        top_ports: Select = select(self.model.port, func.count(self.model.port).label("count")).group_by(self.model.port).order_by(desc("count")).filter(self.model.project_id == project_id, self.model.scan_id == last_scan_id)
        result = await self._session.exec(top_ports)
        top_ports_result = result.all()
        return top_ports_result


    async def resource_list(self, project_id: str):
        stmt = select(
                Port.id,
                IP.ip,
                Port.port,
                Domain.domain,
                func.count(L4SoftwareVulnerability.id).label('cnt')).select_from(Port)\
            .join(IP, IP.id == Port.ip_id)\
            .join(DNS_A, DNS_A.target_ip_id == IP.id, isouter=True)\
            .join(Domain, Domain.id == DNS_A.target_domain_id, isouter=True)\
            .join(L4Software, L4Software.l4_id == Port.id, isouter=True)\
            .join(L4SoftwareVulnerability, L4SoftwareVulnerability.l4_software_id == L4Software.id, isouter=True)\
            .filter(Port.project_id == project_id)\
            .group_by(Port.id)
        result = await self._session.exec(stmt)
        return result.all()


    async def vulnerabilities(self, l4_id: str, project_id: str):
        stmt = select(L4SoftwareVulnerability.id.label("abc"), 
                      L4SoftwareVulnerability.confirmed.label("confirmed"),
                      Vendor,
                      Software,
                      Vulnerability)\
        .join(L4SoftwareVulnerability, L4SoftwareVulnerability.vulnerability_id== Vulnerability.id)\
        .join(L4Software, L4Software.id == L4SoftwareVulnerability.l4_software_id)\
        .join(Software, L4Software.software_id == Software.id)\
        .join(Port, Port.id == L4Software.l4_id)\
        .join(Vendor, Vendor.id == Software.vendor_id)\
        .filter(Port.id == l4_id)
        result = await self._session.exec(stmt)
        return result.all()


    async def get_top_protocols(self, project_id: str, last_scan_id: str):
        stmt_protocols = select(
                case(
                    (Port.protocol.is_(None), "unknown"),
                    (Port.protocol == "", "unknown"),
                    else_=Port.protocol
                ).label("labels"),
                func.count(Port.protocol).label("values")
            ).filter(Port.project_id == project_id, Port.scan_id == last_scan_id)\
            .group_by(Port.protocol)\
            .order_by(func.count(Port.protocol).desc()) 

        result = await self._session.exec(stmt_protocols)
        top_protocols_result = result.all()
        return top_protocols_result


    async def get_port_tabulator_data(self, project_id: str, last_scan_id: str):
        row_number_column = func.row_number().over(order_by=func.count(Port.port).desc()).label("id")
        tabulator_dashboard_data = (
                select(
                    row_number_column,
                    IP.ip,
                    Port.port,
                    Port.protocol,
                    Port.service_name,
                )
                .join(Port, IP.id == Port.ip_id)
                .filter(IP.project_id == project_id, IP.scan_id == last_scan_id)
                .group_by(
                    Port.port,
                    Port.protocol,
                    IP.ip,
                    Port.state,
                    Port.service_name,
                )
                .order_by(func.count(Port.port).desc())
            )
        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()


    async def get_resource_for_snmp(self, project_id: str, scan_id: str):
        stmt = select(IP.ip, Port.port).\
                select_from(Port).\
                    join(IP, IP.id == Port.ip_id).\
                        filter(Port.project_id == project_id, Port.scan_id == scan_id, Port.service_name == "snmp", Port.protocol == "udp")
        result = await self._session.exec(stmt)
        return result.all()