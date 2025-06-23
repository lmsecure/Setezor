
from sqlmodel import select
from setezor.models import SoftwareType
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class SoftwareTypeRepository(SQLAlchemyRepository[SoftwareType]):
    model = SoftwareType

    async def exists(self, software_type_obj: SoftwareType):
        stmt = select(SoftwareType).filter_by(name=software_type_obj.name)
        res = await self._session.exec(stmt)
        return res.first()