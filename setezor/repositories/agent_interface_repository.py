from sqlmodel import select

from setezor.models import IP, AgentInProject
from setezor.models.agent_network_interface import AgentInterface
from setezor.repositories import SQLAlchemyRepository


class AgentInterfaceRepository(SQLAlchemyRepository[AgentInterface]):
    model = AgentInterface

    async def exists(self, interface: AgentInterface) -> AgentInterface:
        stmt = select(AgentInterface).filter(
            AgentInterface.agent_id == interface.agent_id,
            AgentInterface.ip == interface.ip,
            AgentInterface.name == interface.name
        )
        result = await self._session.exec(stmt)
        return result.first()

    async def get_interfaces_in_project(self, project_id: str):
        stmt = (select(IP.id, AgentInProject.id.label("agent_id"), AgentInterface.name)
                .join(AgentInProject, AgentInProject.agent_id == AgentInterface.agent_id)
                .join(IP, AgentInterface.id == IP.interface_id)
                .filter(AgentInProject.project_id==project_id, IP.project_id==project_id)
                )
        result = await self._session.exec(stmt)
        return result.all()

    async def get_interfaces_on_agent(self, agent_id: str, project_id: str):
        stmt = (select(AgentInterface.id, IP.ip, AgentInterface.name, IP.id.label("ip_id"), AgentInterface.mac)
                .join(IP, IP.interface_id == AgentInterface.id)
                .filter(AgentInterface.agent_id==agent_id, IP.project_id==project_id))
        result = await self._session.exec(stmt)
        res = result.all()
        return res

    async def find_by_names(self, agent_id: str, interfaces: list[str]):
        query = select(AgentInterface).filter(AgentInterface.name.in_(interfaces), AgentInterface.agent_id == agent_id)
        result = await self._session.exec(query)
        return result.all()