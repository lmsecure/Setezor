from setezor.models.agent_network_interface import AgentInterface
from setezor.network_structures import InterfaceStruct
from setezor.services.base_service import BaseService


class AgentInterfaceService(BaseService):

    async def create(self, agent_interface_model: AgentInterface):
        async with self._uow:
            new_interface = self._uow.agent_interface.add(agent_interface_model.model_dump())
            await self._uow.commit()
            return new_interface

    async def find_by_names(self, agent_id: str, interfaces: list[str]):
        async with self._uow:
            return await self._uow.agent_interface.find_by_names(agent_id=agent_id, interfaces=interfaces)
    
    async def get_interfaces_on_agent(self, project_id: str, agent_id: str):
        async with self._uow:
            return await self._uow.agent_interface.get_interfaces_on_agent(project_id=project_id, agent_id=agent_id)

    async def get_by_agent_id(self, agent_id: str):
        async with self._uow:
            return await self._uow.agent_interface.filter(agent_id=agent_id)
