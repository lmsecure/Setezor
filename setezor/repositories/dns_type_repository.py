from setezor.models import DNS_Type
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class DNS_Type_Repository(SQLAlchemyRepository[DNS_Type]):
    model = DNS_Type


    async def exists(self, dns_type_obj: SQLModel):
        stmt = select(self.model).filter(DNS_Type.name == dns_type_obj.name)
        result = await self._session.exec(stmt)
        return result.first()