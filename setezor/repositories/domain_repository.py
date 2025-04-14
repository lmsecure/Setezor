from setezor.models import Domain, DNS_A, IP
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class DomainRepository(SQLAlchemyRepository[Domain]):
    model = Domain

    async def exists(self, domain_obj: SQLModel):
        if not domain_obj.domain:
            return None
        stmt = select(Domain).filter(Domain.domain == domain_obj.domain, 
                                     Domain.project_id == domain_obj.project_id, 
                                     Domain.scan_id == domain_obj.scan_id)
        result = await self._session.exec(stmt)
        return result.first()


    async def get_node_info(self, ip_id: str, project_id: str):
        stmt = select(Domain).select_from(IP)\
            .join(DNS_A, DNS_A.target_ip_id == IP.id)\
            .join(Domain, DNS_A.target_domain_id == Domain.id)\
            .filter(IP.id == ip_id, IP.project_id == project_id)
        result = await self._session.exec(stmt)
        return result.all()