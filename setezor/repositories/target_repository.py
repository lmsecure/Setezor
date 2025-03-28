from sqlalchemy import ScalarResult
from setezor.models import Target, Scope
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, and_, select

class TargetRepository(SQLAlchemyRepository[Target]):
    model = Target

    async def get_cert_scope_data(self, project_id: str):
        base_filter = and_(
            Target.project_id == project_id,
            Target.protocol == 'https',
            Target.port.isnot(None)
        )

        ip = Target.ip

        if ip:
            stmt = (
                select(
                    Target.protocol,
                    Target.ip,
                    Target.port,
                )
                .join(Scope, Target.scope_id == Scope.id)
                .filter(base_filter, Target.ip.isnot(None))
            )
        else:
            stmt = (
                select(
                    Target.protocol,
                    Target.domain,
                    Target.port,
                )
                .join(Scope, Target.scope_id == Scope.id)
                .filter(base_filter, Target.domain.isnot(None))
            )

        result = await self._session.exec(stmt)
        return result.all()
    
    async def for_scope(self, project_id: str, scope_id: str):
        stmt = select(self.model).filter(self.model.project_id == project_id, 
                                         self.model.scope_id == scope_id,
                                         self.model.deleted_at == None)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()