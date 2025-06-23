from setezor.services.base_service import BaseService


class AgentParentAgentService(BaseService):
    async def create(self, agent_parent_agent):
        async with self._uow:
            new_agent_parent_agent = self._uow.agent_parent_agent.add(agent_parent_agent.model_dump())
            await self._uow.commit()
            return new_agent_parent_agent