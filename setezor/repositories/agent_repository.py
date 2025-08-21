from setezor.models import Agent
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import aliased


class AgentRepository(SQLAlchemyRepository[Agent]):
    model = Agent

    async def exists(self, dns_obj: SQLModel):
        return False

    async def list(self, user_id: str):
        stmt = select(Agent).filter(self.model.user_id == user_id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()

    async def user_settings_page(self, user_id: str) -> list:
        stmt = select(Agent).filter(Agent.user_id == user_id, Agent.secret_key != "")
        res = await self._session.exec(stmt)
        return res.all()
    
    async def user_connected_agents(self, user_id: str) -> list:
        stmt = select(Agent).filter(Agent.user_id == user_id, Agent.is_connected == True, Agent.secret_key != "")
        res = await self._session.exec(stmt)
        return res.all()

    async def settings_page(self, project_id: str):
        ParentAgent = aliased(Agent)
        stmt = select(Agent, ParentAgent)\
            .join(ParentAgent, ParentAgent.id == Agent.parent_agent_id, isouter=True)\
            .filter(self.model.project_id == project_id)
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()

    async def possible_parent_agents(self, agent_id: str, user_id: str):
        stmt = select(Agent).filter(Agent.id != agent_id, Agent.user_id == user_id, Agent.secret_key != "")
        res: ScalarResult = await self._session.exec(stmt)
        return res.all()