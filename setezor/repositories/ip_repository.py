from sqlalchemy import Select
from setezor.models import IP, MAC, Agent, Network, RouteList, Route, Object, ObjectType, Port, DNS_A, DNS_NS, Domain, AgentInProject
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import select, func, or_


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
            stmt = select(IP).join(MAC, IP.mac_id == MAC.id).filter(IP.ip == ip, 
                                                                    MAC.mac == mac, 
                                                                    IP.project_id == ip_obj.project_id,
                                                                    IP.scan_id==ip_obj.scan_id
                                                                    )
        result = await self._session.exec(stmt)
        return result.first()


    async def vis_nodes_and_interfaces(self, project_id: str, scans: list[str]):
        stmt_for_get_agents_for_interfaces = select(IP.id.label("ip_id"), AgentInProject.id.label("agent_id")).select_from(IP)\
            .join(MAC, IP.mac_id == MAC.id)\
            .join(AgentInProject, MAC.object_id == AgentInProject.object_id)\
            .filter(IP.project_id == project_id)
        addition = [IP.scan_id == scan_id for scan_id in scans]
        addition.append(IP.scan_id == None)
        stmt_for_get_agents_for_interfaces = stmt_for_get_agents_for_interfaces.filter(or_(*addition))
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
        return (await self._session.exec(stmt_for_get_nodes)).all()


    async def get_node_info(self, ip_id: str, project_id: str) -> dict:
        stmt = select(IP, MAC, Network)\
            .select_from(IP)\
                .join(Network, IP.network_id==Network.id)\
                    .join(MAC, IP.mac_id == MAC.id)\
            .filter(IP.id == ip_id, IP.project_id==project_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_ip_count(self, project_id: str, last_scan_id: str):
        """Считает количество сток"""
        ip_count: Select = select(func.count()).select_from(self.model).filter(self.model.project_id == project_id, self.model.scan_id == last_scan_id)
        result = await self._session.exec(ip_count)
        ip_count_result = result.one()
        return ip_count_result


    async def get_ip_mac_port_data(
        self,
        project_id: str,
        last_scan_id: str,
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
            .filter(IP.project_id == project_id, IP.scan_id == last_scan_id, IP.ip != None)
        
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
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        
        total = await self._session.scalar(count_query)
        result = await self._session.exec(paginated_query)
        return total, result.all()



    async def get_domain_ip_data(
        self,
        project_id: str,
        last_scan_id: str,
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "ipaddr": IP.ip,
            "port": Port.port,
            "domain": Domain.domain,
        }
        
        stmt = select(IP.ip, Port.port, Domain.domain).select_from(IP)\
            .join(Port, IP.id == Port.ip_id, isouter=True)\
            .join(DNS_A, DNS_A.target_ip_id == IP.id, isouter=True)\
            .join(Domain, Domain.id == DNS_A.target_domain_id, isouter=True)\
            .filter(IP.project_id == project_id, IP.scan_id == last_scan_id, Domain.domain != "")
        
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