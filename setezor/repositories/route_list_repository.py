from setezor.models import RouteList, Agent, IP, MAC, AgentInProject, AgentParentAgent
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, or_, select
from sqlalchemy.orm import aliased


class RouteListRepository(SQLAlchemyRepository[RouteList]):
    model = RouteList

    async def exists(self, route_list_obj: SQLModel):
        return False

    async def vis_edge_agent_to_agent(self, project_id: str):
        Agent_from = aliased(AgentInProject)
        Agent_to = aliased(AgentInProject)
        query = select(Agent_from.id, Agent_to.id).select_from(Agent)\
                .join(AgentParentAgent, AgentParentAgent.parent_agent_id == Agent.id, isouter=True)\
                .join(Agent_from, Agent_from.agent_id == Agent.id)\
                .join(Agent_to, Agent_to.agent_id == AgentParentAgent.agent_id, isouter=True)\
            .filter(Agent_from.project_id==project_id, Agent_to.project_id==project_id, AgentParentAgent.deleted_at == None)
        return (await self._session.exec(query)).all()

    async def vis_edge_agent_to_interface(self, project_id: str):
        query = select(AgentInProject.id, IP.id)\
        .join(MAC, IP.mac_id == MAC.id)\
        .join(AgentInProject, AgentInProject.object_id == MAC.object_id).filter(IP.project_id==project_id)
        return await self._session.exec(query)

    async def vis_edge_node_to_node(self, project_id: str, scans: list[str]):
        query = select(RouteList.ip_id_from, RouteList.ip_id_to).filter(RouteList.project_id == project_id)
        addition = [RouteList.scan_id == scan_id for scan_id in scans]
        addition.append(RouteList.scan_id == None)
        query = query.filter(or_(*addition))
        return await self._session.exec(query)
