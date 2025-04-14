from setezor.models import AgentParentAgent, Agent, User
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import aliased


class AgentParentAgentRepository(SQLAlchemyRepository[AgentParentAgent]):
    model = AgentParentAgent

    async def exists(self, dns_obj: SQLModel):
        return False

    async def get_graph(self, user_id: str):
        PAgent = aliased(Agent)
        stmt = select(Agent.id, AgentParentAgent.parent_agent_id)\
            .select_from(AgentParentAgent)\
            .join(Agent, Agent.id == AgentParentAgent.agent_id)\
            .join(PAgent, PAgent.id == AgentParentAgent.parent_agent_id)\
            .filter(Agent.user_id == user_id, 
                    PAgent.is_connected == True, 
                    AgentParentAgent.deleted_at == None)
        res = await self._session.exec(stmt)
        return res.all()
    
    async def get_parents_for_user_agent(self, agent_id: str, user_id: str):
        PAgent = aliased(Agent)
        stmt = select(PAgent.rest_url)\
            .select_from(AgentParentAgent)\
            .join(Agent, Agent.id == AgentParentAgent.agent_id)\
            .join(PAgent, PAgent.id == AgentParentAgent.parent_agent_id)\
            .filter(Agent.user_id == user_id, 
                    Agent.id == agent_id, 
                    AgentParentAgent.deleted_at == None)
        res = await self._session.exec(stmt)
        return res.all()
