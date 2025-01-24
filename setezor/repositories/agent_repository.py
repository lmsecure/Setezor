from setezor.models import Agent
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import aliased

class AgentRepository(SQLAlchemyRepository[Agent]):
    model = Agent

    async def exists(self, dns_obj: SQLModel):
        return False
    
    async def list(self, project_id: str):
        stmt = select(Agent).filter(self.model.project_id == project_id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()
    
    async def settings_page(self, project_id: str):
        ParentAgent= aliased(Agent)
        stmt = select(Agent, ParentAgent)\
        .join(ParentAgent, ParentAgent.id == Agent.parent_agent_id, isouter=True)\
        .filter(self.model.project_id == project_id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()