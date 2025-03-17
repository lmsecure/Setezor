from sqlalchemy import ScalarResult
from setezor.models import Scope
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class ScopeRepository(SQLAlchemyRepository[Scope]):
    model = Scope

    async def project_scopes(self, project_id: str):
        stmt = select(self.model).filter(self.model.project_id == project_id, 
                                         self.model.deleted_at == None)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()
