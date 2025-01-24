import uuid
from sqlalchemy import Select
from setezor.models import WhoIsDomain
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult

class WhoisDomainRepository(SQLAlchemyRepository[WhoIsDomain]):
    model = WhoIsDomain

    async def exists(self, mac_obj: SQLModel):
        return False
    
    async def get_whois_domain_data(self, project_id: uuid.UUID):
        
        whois_domain: Select = select(self.model.domain_crt, self.model.data)\
        .filter(self.model.project_id == project_id)\

        result = await self._session.exec(whois_domain)
        whois_domain_data_result = result.all()
        return whois_domain_data_result