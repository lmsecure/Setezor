from setezor.models import Agent, AgentParentAgent
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


    async def get_all_heirs(self, user_id: str, agent_id: str) -> list:
        agent_stmt = select(AgentParentAgent.parent_agent_id, AgentParentAgent.agent_id)\
            .join(Agent, AgentParentAgent.parent_agent_id == Agent.id)\
            .filter(Agent.user_id == user_id)
        agent_stmt_exec: ScalarResult = await self._session.exec(agent_stmt)
        agent_ids = agent_stmt_exec.all()

        links = {}
        for parent_id, child_id in agent_ids:
            if parent_id in links:
                links[parent_id].append(child_id)
            else:
                links.update({parent_id : [child_id]})

        def collect_heirs(graph: list[tuple], start_id: str) -> list:
            visited = set()
            stack = [start_id]
            result = set()
            while stack:
                current = stack.pop()
                for nxt in graph.get(current, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        result.add(nxt)
                        stack.append(nxt)
            result.discard(start_id)
            return list(result)

        applicants = collect_heirs(graph=links, start_id=agent_id)
        result_stmt = select(Agent.id, Agent.name).filter(Agent.id.in_(applicants), Agent.deleted_at.is_(None))
        result_exec: ScalarResult = await self._session.exec(result_stmt)
        result = result_exec.all()
        return result
