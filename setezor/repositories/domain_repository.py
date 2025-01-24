from setezor.models import Domain
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