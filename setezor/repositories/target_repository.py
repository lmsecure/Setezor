from sqlalchemy import ScalarResult, func
from setezor.models import Target, Scope
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, and_, select

from setezor.schemas.pagination import PaginatedResponse

class TargetRepository(SQLAlchemyRepository[Target]):
    model = Target

    async def for_scope_filtred(self, project_id: str, scope_id: str, page: int = 1, limit: int = 50):
        base_stmt = select(self.model).filter(
            self.model.project_id == project_id,
            self.model.scope_id == scope_id,
            self.model.deleted_at == None
        )
        
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self._session.exec(count_stmt)
        total = total_result.one()
        
        offset = (page - 1) * limit
        stmt = base_stmt.offset(offset).limit(limit)
        res: ScalarResult = await self._session.exec(stmt)
        data = res.all()
        
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return PaginatedResponse(
            data=data,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    async def for_scope(self, project_id: str, scope_id: str):
        stmt = select(self.model).filter(self.model.project_id == project_id, 
                                         self.model.scope_id == scope_id,
                                         self.model.deleted_at == None)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()