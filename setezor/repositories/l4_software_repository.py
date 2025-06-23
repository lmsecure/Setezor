
from sqlalchemy import case, func, literal, text
from setezor.models import L4Software, Port, IP, SoftwareVersion, Software, SoftwareType, Vendor, Vulnerability, L4SoftwareVulnerability, DNS_A, Domain, VulnerabilityLink
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, cast, String

class L4SoftwareRepository(SQLAlchemyRepository[L4Software]):
    model = L4Software

    async def exists(self, L4Software_obj: L4Software):
        if not (L4Software_obj.l4_id and L4Software_obj.software_version_id):
            return False
        stmt = select(L4Software).filter(L4Software.l4_id == L4Software_obj.l4_id,
                                         L4Software.software_version_id == L4Software_obj.software_version_id,
                                         L4Software.scan_id == L4Software_obj.scan_id,
                                         L4Software.project_id == L4Software_obj.project_id)
        result = await self._session.exec(stmt)
        return result.first()

    async def get_l4_software_tabulator_data(
        self, 
        project_id: str, 
        last_scan_id: str, 
        page: int, 
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        row_number_column = func.row_number().over(
            order_by=func.count(IP.ip).desc()
        ).label("id")

        field_mapping = {
            "ipaddr": IP.ip,
            "domain": Domain.domain,
            "port": Port.port,
            "protocol": Port.protocol,
            "state": Port.state,
            "service_name": Port.service_name,
            "vendor": Vendor.name,
            "product": Software.product,
            "type": SoftwareType.name,
            "version": SoftwareVersion.version,
            "build": SoftwareVersion.build,
            "cpe23": SoftwareVersion.cpe23,
        }

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
                SoftwareType.name,
                SoftwareVersion.version,
                SoftwareVersion.build,
                SoftwareVersion.cpe23,
                func.count(Port.port).label("port_count"),
                func.count(Port.service_name).label("service_name_count"),
            ).select_from(Port)
            .join(IP, Port.ip_id == IP.id)
            .join(DNS_A, DNS_A.target_ip_id == IP.id)
            .join(Domain, Domain.id == DNS_A.target_domain_id, isouter=True)
            .join(L4Software, Port.id == L4Software.l4_id, isouter=True)
            .join(SoftwareVersion, L4Software.software_version_id == SoftwareVersion.id, isouter=True)
            .join(Software, SoftwareVersion.software_id == Software.id, isouter=True)
            .join(SoftwareType, Software.type_id == SoftwareType.id, isouter=True)
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
                SoftwareType.name,
                SoftwareVersion.version,
                SoftwareVersion.build,
                SoftwareVersion.cpe23,
                Vendor.name,
            )
        )

        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                
                if field in field_mapping and value is not None:
                    column = field_mapping[field]
                    
                    if type_op == "=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column == value)
                    elif type_op == "!=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column != value)
                    elif type_op == ">":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column > value)
                    elif type_op == ">=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column >= value)
                    elif type_op == "<":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column < value)
                    elif type_op == "<=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column <= value)
                    elif type_op == "like":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(
                            column.ilike(f"%{value}%")
                        )

        if sort_params:
            order_clauses = []
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")
                
                if field in field_mapping:
                    column = field_mapping[field]
                    if direction == "desc":
                        order_clauses.append(column.desc())
                    else:
                        order_clauses.append(column.asc())
            
            if order_clauses:
                tabulator_dashboard_data = tabulator_dashboard_data.order_by(*order_clauses)
        else:
            tabulator_dashboard_data = tabulator_dashboard_data.order_by(func.count(IP.ip).desc())

        count_query = select(func.count()).select_from(tabulator_dashboard_data.alias())
        
        offset = (page - 1) * size
        paginated_query = tabulator_dashboard_data.offset(offset).limit(size)

        total = await self._session.scalar(count_query)
        result = await self._session.exec(paginated_query)
        
        return total, result.all()

    async def get_soft_vuln_link_data(
        self,
        project_id: str,
        last_scan_id: str,
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "vendor": Vendor.name,
            "product": Software.product,
            "type": SoftwareType.name,
            "version": SoftwareVersion.version,
            "build": SoftwareVersion.build,
            "cpe23": SoftwareVersion.cpe23,
            "vulnerability_name": Vulnerability.name,
            "cve": Vulnerability.cve,
            "cwe": Vulnerability.cwe,
            "link": VulnerabilityLink.link,
        }
        
        stmt = select(
            Vendor.name,
            Software.product,
            SoftwareType.name,
            SoftwareVersion.version,
            SoftwareVersion.build,
            SoftwareVersion.cpe23,
            Vulnerability.name.label("vulnerability_name"),
            Vulnerability.cve,
            Vulnerability.cwe,
            VulnerabilityLink.link
        ).select_from(Vulnerability)\
            .join(VulnerabilityLink, Vulnerability.id == VulnerabilityLink.vulnerability_id, isouter=True)\
            .join(L4SoftwareVulnerability, L4SoftwareVulnerability.vulnerability_id == Vulnerability.id)\
            .join(L4Software, L4Software.id == L4SoftwareVulnerability.l4_software_id)\
            .join(SoftwareVersion, L4Software.software_version_id == SoftwareVersion.id)\
            .join(Software, SoftwareVersion.software_id == Software.id)\
            .join(SoftwareType, Software.type_id == SoftwareType.id)\
            .join(Vendor, Vendor.id == Software.vendor_id)\
            .filter(L4Software.project_id == project_id, L4Software.scan_id == last_scan_id)
        
        # Применяем фильтры
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                
                if field in field_mapping and value is not None:
                    column = field_mapping[field]
                    
                    if type_op == "=":
                        stmt = stmt.filter(column == value)
                    elif type_op == "!=":
                        stmt = stmt.filter(column != value)
                    elif type_op == ">":
                        stmt = stmt.filter(column > value)
                    elif type_op == ">=":
                        stmt = stmt.filter(column >= value)
                    elif type_op == "<":
                        stmt = stmt.filter(column < value)
                    elif type_op == "<=":
                        stmt = stmt.filter(column <= value)
                    elif type_op == "like":
                        stmt = stmt.filter(column.ilike(f"%{value}%"))
        
        # Применяем сортировку
        if sort_params:
            order_clauses = []
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")
                
                if field in field_mapping:
                    column = field_mapping[field]
                    if direction == "desc":
                        order_clauses.append(column.desc())
                    else:
                        order_clauses.append(column.asc())
            
            if order_clauses:
                stmt = stmt.order_by(*order_clauses)
        
        count_query = select(func.count()).select_from(stmt.alias())
        total = await self._session.scalar(count_query)
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        result = await self._session.exec(paginated_query)
        return total, result.all()



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
            .join(SoftwareVersion, L4Software.software_version_id == SoftwareVersion.id)\
            .join(Software, SoftwareVersion.software_id == Software.id)\
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
            .join(SoftwareVersion, L4Software.software_version_id == SoftwareVersion.id)\
            .join(Software, SoftwareVersion.software_id == Software.id)\
            .filter(Port.project_id == project_id, Port.scan_id == last_scan_id)\
            .group_by(Software.product, Port.service_name)

        stmt = stmt1.union(stmt2)
        stmt = select(text("labels"), text("parent"), func.sum(text("value")).label("value"))\
            .select_from(stmt).group_by(text("labels"), text("parent"))
        result = await self._session.exec(stmt)
        return result.all()