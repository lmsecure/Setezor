from typing import List
from sqlmodel import func, literal, select
from sqlalchemy.orm import aliased

from setezor.models import DNS, IP, Domain, WhoIsDomain, WhoIsIP
from setezor.db.entities import DNSTypes
from setezor.repositories import SQLAlchemyRepository


class DNSRepository(SQLAlchemyRepository[DNS]):
    model = DNS

    async def exists(self, new_dns_obj: DNS) -> bool:
        if new_dns_obj.id:
            return False

        conditions = [self.model.project_id == new_dns_obj.project_id,
                      self.model.scan_id == new_dns_obj.scan_id]
        if new_dns_obj.dns_type_id == DNSTypes.TXT:
            conditions.append(self.model.extra_data == new_dns_obj.extra_data)

        if new_dns_obj.target_domain_id:
            conditions.append(self.model.target_domain_id == new_dns_obj.target_domain_id)
        if new_dns_obj.value_domain_id:
            conditions.append(self.model.value_domain_id == new_dns_obj.value_domain_id)
        if new_dns_obj.target_ip_id:
            conditions.append(self.model.target_ip_id == new_dns_obj.target_ip_id)

        stmt = select(self.model)
        if new_dns_obj.target_domain:
            TargetDomain = aliased(Domain)
            stmt = stmt.join(TargetDomain, self.model.target_domain_id == TargetDomain.id)\
                .filter(TargetDomain.domain == new_dns_obj.target_domain.domain)
        if new_dns_obj.value_domain:
            ValueDomain = aliased(Domain)
            stmt = stmt.join(ValueDomain, self.model.value_domain_id == ValueDomain.id)\
                .filter(ValueDomain.domain == new_dns_obj.value_domain.domain)
        if new_dns_obj.target_ip:
            stmt = stmt.join(IP, self.model.target_ip_id == IP.id)\
                .filter(IP.ip == new_dns_obj.target_ip.ip)

        stmt = stmt.filter(*conditions)
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj


    async def get_all_whois_data_independent(
        self,
        project_id: str,
        scans: List[str],
        page: int,
        size: int,
        sort_params: list = None,
        filter_params: list = None
    ):
        field_mapping = {
            "ipaddr": "ipaddr",
            "domain": "domain", 
            "AS": "AS",
            "org_name": "org_name",
            "data": "data",
            "range_ip": "range_ip",
            "source": "source"
        }
        
        domain_stmt = select(
            literal(None).label('ipaddr'),
            WhoIsDomain.domain_crt.label('domain'),
            WhoIsDomain.AS.label('AS'),
            WhoIsDomain.org_name.label('org_name'),
            WhoIsDomain.data.label('data'),
            WhoIsDomain.range_ip.label('range_ip'),
            literal('domain').label('source')
        ).select_from(WhoIsDomain).filter(WhoIsDomain.project_id == project_id, WhoIsDomain.scan_id.in_(scans))

        
        ip_stmt = select(
            WhoIsIP.domain_crt.label('ipaddr'),
            literal(None).label('domain'),
            WhoIsIP.AS.label('AS'),
            WhoIsIP.org_name.label('org_name'),
            WhoIsIP.data.label('data'),
            WhoIsIP.range_ip.label('range_ip'),
            literal('ip').label('source')
        ).select_from(WhoIsIP).filter(WhoIsIP.project_id == project_id, WhoIsIP.scan_id.in_(scans))
        
        combined_stmt = domain_stmt.union_all(ip_stmt)
        
        subquery = combined_stmt.subquery('whois_combined')
        
        stmt = select(
            subquery.c.ipaddr,
            subquery.c.domain,
            subquery.c.AS,
            subquery.c.org_name,
            subquery.c.data,
            subquery.c.range_ip,
            subquery.c.source
        )
        
        if filter_params:
            for filter_item in filter_params:
                field = filter_item.get("field")
                type_op = filter_item.get("type", "=")
                value = filter_item.get("value")
                
                if field in field_mapping and value is not None:
                    column = subquery.c[field]
                    
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
                    column = subquery.c[field]
                    if direction == "desc":
                        order_clauses.append(column.desc())
                    else:
                        order_clauses.append(column.asc())
            
            if order_clauses:
                stmt = stmt.order_by(*order_clauses)
        
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_query)
        
        offset = (page - 1) * size
        paginated_query = stmt.offset(offset).limit(size)
        
        result = await self._session.exec(paginated_query)
        paginated_data = result.all()
        
        merged_data = {}
        
        for row in paginated_data:
            key = (row.ipaddr, row.domain)
            
            if key not in merged_data:
                merged_data[key] = {
                    'ipaddr': row.ipaddr,
                    'domain': row.domain,
                    'AS': row.AS,
                    'org_name': row.org_name,
                    'data': row.data,
                    'range_ip': row.range_ip,
                    'source': row.source
                }
            else:
                existing = merged_data[key]
                if row.source == 'domain':
                    existing['AS'] = row.AS if row.AS is not None else existing['AS']
                    existing['org_name'] = row.org_name if row.org_name is not None else existing['org_name']
                    existing['data'] = row.data if row.data is not None else existing['data']
                    existing['range_ip'] = row.range_ip if row.range_ip is not None else existing['range_ip']
                    existing['domain'] = row.domain if row.domain is not None else existing['domain']
                    existing['source'] = 'both'
                elif existing['source'] == 'ip' and row.source == 'ip':
                    existing['ipaddr'] = row.ipaddr if row.ipaddr is not None else existing['ipaddr']
                    existing['AS'] = existing['AS'] if existing['AS'] is not None else row.AS
                    existing['org_name'] = existing['org_name'] if existing['org_name'] is not None else row.org_name
                    existing['data'] = existing['data'] if existing['data'] is not None else row.data
                    existing['range_ip'] = existing['range_ip'] if existing['range_ip'] is not None else row.range_ip
        
        final_data = []
        for data in merged_data.values():
            whois_fields = [data['AS'], data['org_name'], data['data'], data['range_ip']]
            if any(field is not None and str(field).strip() != '' for field in whois_fields):
                final_data.append(data)
        
        return total, final_data
