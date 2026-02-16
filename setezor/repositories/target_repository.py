from sqlalchemy import ScalarResult, func
from setezor.models import Target, Scope
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, and_, select

from setezor.schemas.pagination import PaginatedResponse

class TargetRepository(SQLAlchemyRepository[Target]):
    model = Target

    async def for_scope_filtred(
        self, 
        project_id: str, 
        scope_id: str, 
        page: int = 1, 
        limit: int = 50,
        protocol_filter: str | None = None,
        ip_filter: str | None = None,
        domain_filter: str | None = None,
        port_filter: int | None = None
    ):
        def escape_like(val: str) -> str:
            return val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        
        stmt = select(self.model).filter(
            self.model.project_id == project_id,
            self.model.scope_id == scope_id,
            self.model.deleted_at == None
        )
        
        if protocol_filter and (p := protocol_filter.strip()):
            stmt = stmt.where(self.model.protocol.ilike(f"%{escape_like(p)}%", escape="\\"))
        if ip_filter and (i := ip_filter.strip()):
            stmt = stmt.where(self.model.ip.ilike(f"%{escape_like(i)}%", escape="\\"))
        if domain_filter and (d := domain_filter.strip()):
            stmt = stmt.where(self.model.domain.ilike(f"%{escape_like(d)}%", escape="\\"))
        if port_filter is not None:
            stmt = stmt.where(self.model.port == port_filter)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.exec(count_stmt)).one()
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        
        data = (await self._session.exec(stmt)).all()
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