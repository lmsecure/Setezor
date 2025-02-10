from setezor.models import RouteList, Agent, IP, MAC
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, or_, select
from sqlalchemy.orm import aliased


class RouteListRepository(SQLAlchemyRepository[RouteList]):
    model = RouteList

    async def exists(self, route_list_obj: SQLModel):
        return False
    
    async def vis_edge_agent_to_agent(self, project_id: str):
        a1 = aliased(Agent)
        query = select(Agent.id, a1.id).join(a1, Agent.id == a1.parent_agent_id).filter(Agent.project_id==project_id)
        return (await self._session.exec(query)).all()
    
    async def vis_edge_agent_to_interface(self, project_id: str):
        query = select(IP.id, Agent.id)\
        .join(MAC, IP.mac_id == MAC.id)\
        .join(Agent, Agent.object_id == MAC.object_id).filter(IP.project_id==project_id)
        return await self._session.exec(query)

    async def vis_edge_node_to_node(self, project_id: str, scans: list[str]):
        query = select(RouteList.ip_id_from, RouteList.ip_id_to).filter(RouteList.project_id == project_id)
        addition = [RouteList.scan_id == scan_id for scan_id in scans]
        addition.append(RouteList.scan_id == None)
        query = query.filter(or_(*addition))
        return await self._session.exec(query)
    