from setezor.models import ObjectType
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class ObjectTypeRepository(SQLAlchemyRepository[ObjectType]):
    model = ObjectType


    async def exists(self, object_type_obj: SQLModel):
        stmt = select(self.model).filter_by(name=object_type_obj.name)
        result = await self._session.exec(stmt)
        return result.first()