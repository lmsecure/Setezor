from typing import List
from sqlmodel import func, literal, select
from sqlalchemy.orm import aliased
from sqlalchemy import collate

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
