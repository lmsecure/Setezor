import ipaddress
from typing import List
from sqlalchemy import Select, collate
from setezor.models import IP, MAC, Agent, Network, RouteList, Route, Object, ObjectType, Port, DNS, Domain, AgentInProject, DNS_Type, ASN, WhoIsIP
from setezor.models.node_comment import NodeComment
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import case, select, func, or_, and_
from sqlalchemy.orm import aliased



class IPRepository(SQLAlchemyRepository[IP]):
    model = IP

    async def exists(self, ip_obj: IP):
        if not ip_obj.ip: return None
        ip = ip_obj.ip
        mac = ip_obj.mac.mac if ip_obj.mac else ''
        mac_id = ip_obj.mac_id
        if mac_id:
            stmt = select(IP).join(MAC, IP.mac_id == MAC.id).filter(IP.ip == ip, 
                                                                    IP.mac_id == mac_id, 
                                                                    IP.project_id == ip_obj.project_id,
                                                                    IP.scan_id==ip_obj.scan_id
                                                                    )
        else:
            if ipaddress.ip_address(ip).is_private:  # RFC1918
                stmt = select(IP).filter(IP.ip == ip,
                                         IP.project_id == ip_obj.project_id,
                                         IP.scan_id == ip_obj.scan_id
                                         )
                result = await self._session.exec(stmt)
                ip_from_db = result.first()
                if ip_from_db and ip_from_db.mac_id:
                    mac_stmt = select(MAC).where(MAC.id == ip_from_db.mac_id)
                    result = await self._session.exec(mac_stmt)
                    mac_from_db = result.first()
                    if mac != '' and mac_from_db != mac:
                        mac_from_db.mac = mac
                return ip_from_db
            stmt = select(IP).join(MAC, IP.mac_id == MAC.id).filter(IP.ip == ip,
                                                                    MAC.mac == mac,
                                                                    IP.project_id == ip_obj.project_id,
                                                                    IP.scan_id == ip_obj.scan_id
                                                                    )
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj


    async def vis_nodes_and_interfaces(self, project_id: str, scans: list[str]):
        stmt_for_get_agents_for_interfaces = select(IP.id.label("ip_id"), AgentInProject.id.label("agent_id")).select_from(IP)\
            .join(MAC, IP.mac_id == MAC.id)\
            .join(Object, Object.id == MAC.object_id)\
            .join(AgentInProject, Object.agent_id == AgentInProject.id)\
            .filter(IP.project_id == project_id)
        # addition = [IP.scan_id == scan_id for scan_id in scans]
        # addition.append(IP.scan_id == None)
        # stmt_for_get_agents_for_interfaces = stmt_for_get_agents_for_interfaces.filter(or_(*addition))
        stmt_for_get_nodes_from = select(RouteList.ip_id_from.label("ip_id"), Route.agent_id.label("agent_id")).select_from(RouteList)\
            .join(Route, RouteList.route_id == Route.id).filter(RouteList.project_id == project_id)
        stmt_for_get_nodes_to = select(RouteList.ip_id_to.label("ip_id"), Route.agent_id.label("agent_id")).select_from(RouteList)\
            .join(Route, RouteList.route_id == Route.id).filter(RouteList.project_id == project_id)
        addition = [RouteList.scan_id == scan_id for scan_id in scans]
        addition.append(RouteList.scan_id == None)
        stmt_for_get_nodes_from = stmt_for_get_nodes_from.filter(or_(*addition))
        stmt_for_get_nodes_to = stmt_for_get_nodes_to.filter(or_(*addition))
        stmt_for_get_agents_for_nodes = stmt_for_get_agents_for_interfaces.union(stmt_for_get_nodes_from, stmt_for_get_nodes_to)
        return await self._session.exec(stmt_for_get_agents_for_nodes)


    async def get_nodes(self, project_id: str, scans: list[str]) -> list:
        stmt_for_get_nodes = select(IP.id, IP.ip, Network.start_ip, Network.mask, MAC.mac, ObjectType.name)\
            .join(Network, IP.network_id == Network.id)\
            .join(MAC, IP.mac_id == MAC.id)\
            .join(Object, MAC.object_id == Object.id)\
            .join(ObjectType, Object.object_type_id == ObjectType.id)\
            .filter(IP.project_id == project_id, IP.ip != '')
        addition = [IP.scan_id == scan_id for scan_id in scans]
        addition.append(IP.scan_id == None)
        stmt_for_get_nodes = stmt_for_get_nodes.filter(or_(*addition))
        stmt_for_get_interfaces = select(IP.id, IP.ip, Network.start_ip, Network.mask, MAC.mac, ObjectType.name)\
            .join(Network, IP.network_id == Network.id)\
            .join(MAC, IP.mac_id == MAC.id)\
            .join(Object, MAC.object_id == Object.id)\
            .join(ObjectType, Object.object_type_id == ObjectType.id)\
            .filter(IP.project_id == project_id, IP.ip != '', Object.agent_id != None)
        stmt_for_all_nodes = stmt_for_get_nodes.union(stmt_for_get_interfaces)
        return (await self._session.exec(stmt_for_all_nodes)).all()


    async def get_node_info(self, ip_id: str, project_id: str) -> dict:
        stmt = select(IP, MAC, Network)\
            .select_from(IP)\
                .join(Network, IP.network_id==Network.id)\
                    .join(MAC, IP.mac_id == MAC.id)\
            .filter(IP.id == ip_id, IP.project_id==project_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_ip_count(self, project_id: str, scans: list[str]):
        query = select(func.count()).select_from(self.model).filter(self.model.project_id == project_id)
        
        addition = [self.model.scan_id == scan_id for scan_id in scans]
        query = query.filter(or_(*addition))
        result = await self._session.exec(query)
        return result.one()


    async def get_ip_mac_port_data(
        self,
        project_id: str,
        scans: List[str], 
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "ipaddr": IP.ip,
            "port": Port.port,
            "mac": MAC.mac,
        }
        
        stmt = select(IP.ip, Port.port, MAC.mac).select_from(IP)\
            .join(Port, IP.id == Port.ip_id, isouter=True)\
            .join(MAC, IP.mac_id == MAC.id, isouter=True)\
            .filter(IP.project_id == project_id, IP.scan_id.in_(scans), IP.ip != None)
        
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                if (field == 'port'):
                    value = int(value)
                
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
                        if field != "port":
                            stmt = stmt.filter(column.ilike(f"%{value}%"))
        
        if sort_params:
            order_clauses = []
            numeric_fields = {"port"} 
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")
                
                if field in field_mapping:
                    column = field_mapping[field]                
                    if field in numeric_fields:
                        sorted_column = func.coalesce(column, 0)
                    else:
                        sorted_column = func.coalesce(column, "")
                        if field == "ipaddr" and self._session.bind.dialect.name == 'postgresql':
                            sorted_column = collate(sorted_column, 'C')
                    
                    if direction == "desc":
                        order_clauses.append(sorted_column.desc())
                    else:
                        order_clauses.append(sorted_column.asc())
            
            if order_clauses:
                stmt = stmt.order_by(*order_clauses)
        
        count_query = select(func.count()).select_from(stmt.alias())
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        
        total = await self._session.scalar(count_query)
        result = await self._session.exec(paginated_query)
        return total, result.all()

    async def get_domain_ip_data(
        self,
        project_id: str,
        scans: List[str], 
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        TargetDomain = aliased(Domain)
        ValueDomain = aliased(Domain)
        field_mapping = {
            "ipaddr": IP.ip,
            "port": Port.port,
            "domain": TargetDomain.domain,
            "DNS": DNS_Type.name,
            "value": ValueDomain.domain
        }
        stmt = select(IP.ip,
                      Port.port,
                      TargetDomain.domain,
                      DNS_Type.name,
                      ValueDomain.domain,
                      DNS.extra_data,
                      IP.id,
                      func.count(
                        case((NodeComment.deleted_at == None, NodeComment.id))
                        ).label("comments_count")
                      ).select_from(DNS)\
            .join(DNS_Type, DNS_Type.id == DNS.dns_type_id)\
            .outerjoin(IP, IP.id == DNS.target_ip_id)\
            .outerjoin(Port, Port.ip_id == IP.id)\
            .join(TargetDomain, TargetDomain.id == DNS.target_domain_id)\
            .outerjoin(ValueDomain, ValueDomain.id == DNS.value_domain_id)\
            .outerjoin(NodeComment, NodeComment.ip_id == IP.id)\
            .filter(IP.project_id == project_id, IP.scan_id.in_(scans))\
            .group_by(
                IP.ip,
                Port.port,
                TargetDomain.domain,
                DNS_Type.name,
                ValueDomain.domain,
                DNS.extra_data,
                IP.id,
                Port.id
            )
        
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                if (field == 'port'):
                    value = int(value)
                
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
        
        if sort_params:
            order_clauses = []
            numeric_fields = {"port"} 
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")
                
                if field in field_mapping:
                    column = field_mapping[field]                
                    if field in numeric_fields:
                        sorted_column = func.coalesce(column, 0)
                    else:
                        sorted_column = func.coalesce(column, "")
                    if field == "ipaddr" and self._session.bind.dialect.name == 'postgresql':
                        sorted_column = collate(sorted_column, 'C')
                    if direction == "desc":
                        order_clauses.append(sorted_column.desc())
                    else:
                        order_clauses.append(sorted_column.asc())
            
            if order_clauses:
                stmt = stmt.order_by(*order_clauses)
        
        count_query = select(func.count()).select_from(stmt.alias())
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        
        total = await self._session.scalar(count_query)
        result = await self._session.exec(paginated_query)
        return total, result.all()


    async def get_ip_info_tabulator_data(
        self,
        project_id: str,
        scans: List[str],
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ) -> tuple[int, list]:
        addition = [IP.scan_id == scan_id for scan_id in scans]
        stmt = select(
            IP.ip.label("ipaddr"),
            Network.start_ip.label("start_ip"),
            Network.mask.label("mask"),
            ASN.name.label("AS-name"),
            ASN.number.label("AS-number"),
            ASN.org.label("org-name"),
            WhoIsIP.data.label("data")
        ).select_from(IP)\
            .join(Network, Network.id == IP.network_id)\
            .join(ASN, ASN.id == Network.asn_id)\
            .join(WhoIsIP, WhoIsIP.ip_id == IP.id, isouter=True)\
        .filter(IP.project_id == project_id, or_(*addition))

        field_mapping = {
            "ipaddr": IP.ip,
            "AS": ASN.name,
            "AS-number": ASN.number,
            "org-name": ASN.org
        }
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                if field in field_mapping and value is not None:
                    column = field_mapping.get(field)
                    if type_op == "=":
                        stmt = stmt.filter(column == value)
                    elif type_op == "!=":
                        stmt = stmt.filter(column != value)
                    elif type_op == "like":
                        stmt = stmt.filter(column.ilike(f"%{value}%"))
                    elif type_op == ">":
                        stmt = stmt.filter(column > value)
                    elif type_op == ">=":
                        stmt = stmt.filter(column >= value)
                    elif type_op == "<":
                        stmt = stmt.filter(column < value)
                    elif type_op == "<=":
                        stmt = stmt.filter(column <= value)
        if sort_params:
            order_clauses = []
            for sort_item in sort_params:
                field = sort_item.get("field")
                direction = sort_item.get("dir", "asc")
                if field in field_mapping:
                    column = field_mapping.get(field)
                    sorted_column = func.coalesce(column, "")
                    if field == "ipaddr" and self._session.bind.dialect.name == 'postgresql':
                        sorted_column = collate(sorted_column, 'C')
                    if direction == "desc":
                        order_clauses.append(sorted_column.desc())
                    else:
                        order_clauses.append(sorted_column.asc())
            if order_clauses:
                stmt = stmt.order_by(*order_clauses)
        count_query = select(func.count()).select_from(stmt.alias())
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        total = await self._session.scalar(count_query)
        result = await self._session.exec(paginated_query)
        return total, result.all()


    async def get_ip_data(self, project_id: str, last_scan_id: str):
        row_number_column = func.row_number().over(
        order_by=func.count(IP.ip).desc()
        ).label("id")
        tabulator_dashboard_data = (
            select(
                row_number_column,
                IP.ip,
                MAC.mac,
            )
            .outerjoin(Port, IP.id == Port.ip_id)
            .outerjoin(MAC, IP.mac_id == MAC.id)
            .filter(IP.project_id == project_id, IP.scan_id==last_scan_id)
            .group_by(
                IP.ip,
                MAC.mac
            )
            .order_by(func.count(IP.ip).desc())
        )
        result = await self._session.exec(tabulator_dashboard_data)
        return result.all()


    async def get_ips_ports(self, project_id: str):
        stmt = select(IP.ip, Port.port).select_from(Port).join(IP, Port.ip_id == IP.id).filter(Port.project_id == project_id, IP.scan_id != None)
        result = await self._session.exec(stmt)
        return result.all()
    

    async def get_l4_data_for_target(
        self,
        project_id: str,
        scans: List[str],
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "ipaddr": IP.ip,
            "domain": Domain.domain,
            "port": Port.port,
            "protocol": Port.protocol,
            "service_name": Port.service_name
        }
        addition = []
        addition.extend([IP.scan_id == scan_id for scan_id in scans])
        addition.extend([DNS.scan_id == scan_id for scan_id in scans])
        addition.extend([Domain.scan_id == scan_id for scan_id in scans])
        addition.extend([Port.scan_id == scan_id for scan_id in scans])
        tabulator_dashboard_data = (
            select(
                IP.ip,
                Domain.domain,
                Port.port,
                Port.protocol,
                Port.service_name,
                func.count(Port.port).label("port_count")
            )
            .select_from(Port)
            .join(IP, Port.ip_id == IP.id, full=True)
            .join(DNS, DNS.target_ip_id == IP.id, full=True)
            .join(Domain, Domain.id == DNS.target_domain_id, full=True)
            .filter(or_(IP.project_id == project_id,
                        DNS.project_id == project_id,
                        Domain.project_id == project_id,
                        Port.project_id == project_id),
                    or_(*addition),
                    or_(
                        and_(IP.ip != None, IP.ip != ""),
                        and_(Domain.domain != None, Domain.domain != ""),
                        and_(Port.port != None),
                        and_(Port.protocol != None, Port.protocol != ""),
                        and_(Port.service_name != None, Port.service_name != "")))
            .group_by(IP.ip, Domain.domain, Port.port, Port.protocol, Port.service_name)
        )

        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                raw_value = filter_item.get("value")

                if field not in field_mapping or raw_value is None:
                    continue

                column = field_mapping[field]

                if isinstance(raw_value, str) and ',' in raw_value:
                    values = [v.strip() for v in raw_value.split(',') if v.strip()]
                    if not values:
                        continue

                    if field == 'port':
                        try:
                            values = [int(v) for v in values]
                        except ValueError:
                            continue

                    if type_op == "=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column.in_(values))
                    elif type_op == "!=":
                        tabulator_dashboard_data = tabulator_dashboard_data.having(~column.in_(values))
                    elif type_op == "like":
                        or_conditions = [column.ilike(f"%{v}%") for v in values]
                        tabulator_dashboard_data = tabulator_dashboard_data.having(or_(*or_conditions))
                    else:
                        continue
                else:
                    value = raw_value
                    if field == 'port':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            continue

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
                        tabulator_dashboard_data = tabulator_dashboard_data.having(column.ilike(f"%{value}%"))

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