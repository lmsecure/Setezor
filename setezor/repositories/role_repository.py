from setezor.models import Role
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class RoleRepository(SQLAlchemyRepository[Role]):
    model = Role

    async def exists(self, role_obj: SQLModel):
        stmt = select(Role).filter(Role.name == role_obj.name)
        result = await self._session.exec(stmt)
        return result.first()