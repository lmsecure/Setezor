import uuid

from sqlalchemy import Select
from setezor.models import WhoIsIP
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult

class WhoisIPRepository(SQLAlchemyRepository[WhoIsIP]):
    model = WhoIsIP

    async def exists(self, mac_obj: SQLModel):
        return False
    
    async def get_whois_ip_data(self, project_id: uuid.UUID):
        
        whois_ip: Select = select(self.model.domain_crt, self.model.data, self.model.AS, self.model.range_ip,)\
        .filter(self.model.project_id == project_id)\

        result = await self._session.exec(whois_ip)
        whois_ip_data_result = result.all()
        return whois_ip_data_result