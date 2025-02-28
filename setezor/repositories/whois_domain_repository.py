import uuid
from sqlalchemy import Select
from setezor.models import WhoIsDomain
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult

class WhoisDomainRepository(SQLAlchemyRepository[WhoIsDomain]):
    model = WhoIsDomain

    async def exists(self, whois_domain_obj: WhoIsDomain):
        stmt = select(WhoIsDomain).filter(WhoIsDomain.domain_crt==whois_domain_obj.domain_crt,
                                      WhoIsDomain.project_id==whois_domain_obj.project_id,
                                      WhoIsDomain.scan_id==whois_domain_obj.scan_id)
        result = await self._session.exec(stmt)
        return result.first()
    
    async def get_whois_domain_data(self, project_id: uuid.UUID):
        
        whois_domain: Select = select(self.model.domain_crt, self.model.data)\
        .filter(self.model.project_id == project_id)\

        result = await self._session.exec(whois_domain)
        whois_domain_data_result = result.all()
        return whois_domain_data_result