from setezor.models import AgentInProject, Agent, User, AgentParentAgent
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select
from sqlalchemy.orm import aliased, selectinload


class AgentInProjectRepository(SQLAlchemyRepository[AgentInProject]):
    model = AgentInProject

    async def exists(self, dns_obj: SQLModel):
        return False


    async def all_agents(self, list_users: list):
        ParentAgent = aliased(Agent)
        ParentAgentInProject = aliased(AgentInProject)

        stmt = select(Agent, AgentInProject, ParentAgent, ParentAgentInProject).select_from(AgentParentAgent)\
                .join(Agent, Agent.id == AgentParentAgent.agent_id)\
                .join(ParentAgent, ParentAgent.id == AgentParentAgent.parent_agent_id)\
                .join(AgentInProject, AgentInProject.agent_id == Agent.id, isouter=True)\
                .join(ParentAgentInProject, ParentAgentInProject.agent_id == ParentAgent.id, isouter=True)\
            .filter(AgentParentAgent.deleted_at == None, (Agent.user_id.in_(list_users)))\
            .order_by(AgentInProject.created_at)

        res = await self._session.exec(stmt)
        return res.all()


    async def list_for_table(self, project_id: str):
        ParentAgent = aliased(Agent)
        stmt = select(Agent, AgentInProject, ParentAgent, User).select_from(Agent)\
                .join(AgentInProject, AgentInProject.agent_id == Agent.id)\
                .join(AgentParentAgent, AgentParentAgent.agent_id == Agent.id, isouter=True)\
                .join(ParentAgent, ParentAgent.id == AgentParentAgent.parent_agent_id, isouter=True)\
                .join(User, User.id == Agent.user_id, isouter=True)\
            .filter(AgentInProject.project_id == project_id, AgentParentAgent.deleted_at == None)\
            .order_by(AgentInProject.created_at)

        res = await self._session.exec(stmt)
        return res.all()
    
    async def list_for_tasks(self, project_id: str):
        stmt = select(Agent, AgentInProject).select_from(Agent)\
                .join(AgentInProject, AgentInProject.agent_id == Agent.id)\
                .filter(AgentInProject.project_id == project_id)\
                .order_by(AgentInProject.created_at)
        res = await self._session.exec(stmt)
        return res.all()


    async def for_map(self, project_id: str):
        stmt = select(AgentInProject.id, Agent.name, Agent.rest_url, Agent.secret_key).select_from(Agent)\
            .join(AgentInProject, AgentInProject.agent_id == Agent.id)\
            .filter(AgentInProject.project_id == project_id)
        res = await self._session.exec(stmt)
        return res.all()

    async def get_project_agents(self, project_id: str):
        query = select(AgentInProject).where(AgentInProject.project_id == project_id, AgentInProject.deleted_at == None).options(
            selectinload(AgentInProject.agent)
        )
        res = await self._session.exec(query)
        return res.all()
