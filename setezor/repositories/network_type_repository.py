from setezor.models import Network_Type
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class Network_Type_Repository(SQLAlchemyRepository[Network_Type]):
    model = Network_Type


    async def exists(self, network_type_obj: SQLModel):
        stmt = select(Network_Type).filter(Network_Type.name == network_type_obj.name)
        result = await self._session.exec(stmt)
        return result.first()