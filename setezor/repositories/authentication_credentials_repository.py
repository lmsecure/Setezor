
from sqlalchemy import func
from setezor.repositories import SQLAlchemyRepository
from setezor.models import Authentication_Credentials, Port, IP, Domain, DNS_A

from sqlmodel import select



class AuthenticationCredentialsRepository(SQLAlchemyRepository[Authentication_Credentials]):

    model = Authentication_Credentials

    async def exists(self, auth_obj: Authentication_Credentials):
        stmt = select(Authentication_Credentials).filter(Authentication_Credentials.project_id == auth_obj.project_id,
                                                            Authentication_Credentials.scan_id == auth_obj.scan_id,
                                                            Authentication_Credentials.port_id == auth_obj.port_id,
                                                            Authentication_Credentials.login == auth_obj.login,
                                                            Authentication_Credentials.password == auth_obj.password,
                                                            Authentication_Credentials.permissions == auth_obj.permissions,
                                                            Authentication_Credentials.need_auth == auth_obj.need_auth,
                                                            Authentication_Credentials.role == auth_obj.role)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_data_for_tabulator(
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
            "domain": Domain.domain,
            "port": Port.port,
            "login": Authentication_Credentials.login,
            "password": Authentication_Credentials.password,
            "permissions": Authentication_Credentials.permissions,
            "parameters": Authentication_Credentials.parameters,
        }
        
        stmt = select(IP, Domain, Port, Authentication_Credentials).select_from(Port).\
            join(Authentication_Credentials, Port.id == Authentication_Credentials.port_id).\
            join(IP, IP.id == Port.ip_id).\
            join(DNS_A, DNS_A.target_ip_id == IP.id).\
            join(Domain, Domain.id == DNS_A.target_domain_id).\
            filter(Port.project_id == project_id, Port.scan_id == last_scan_id)
        
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
        total = await self._session.scalar(count_query)
        offset = (page - 1) * size
        paginated_stmt = stmt.offset(offset).limit(size)
        result = await self._session.exec(paginated_stmt)
        return total, result.all()


    async def get_credentials_for_node(self, ip_id: str, project_id: str):
        stmt = select(Port, Authentication_Credentials).select_from(Port)\
                .join(Authentication_Credentials, Port.id == Authentication_Credentials.port_id)\
                .filter(Port.project_id == project_id, Port.ip_id == ip_id)
        result = await self._session.exec(stmt)
        return result.all()