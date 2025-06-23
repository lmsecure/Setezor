from typing import List
from Crypto.Random import get_random_bytes
from setezor.services.base_service import BaseService
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.models import Agent, Object, MAC, IP, Network, ASN, DNS_A, Domain
from setezor.models.agent_parent_agent import AgentParentAgent
from setezor.models.base import generate_unique_id
from setezor.schemas.task import WebSocketMessage
from setezor.tools.graph import find_all_paths
from setezor.unit_of_work import UnitOfWork
from setezor.schemas.agent import AgentAdd, AgentParents, InterfaceOfAgent
from setezor.tools.ip_tools import get_network


class AgentService(BaseService):
    async def get_server_agent(self):
        async with self._uow:
            return await self._uow.agent.find_one(name="Server", secret_key="")

    async def list(self, project_id: str) -> list:
        async with self._uow:
            agents = await self._uow.agent.list(project_id=project_id)
            return agents

    async def get(self, id: str) -> Agent:
        async with self._uow:
            return await self._uow.agent.find_one(id=id)

    async def get_by_id(self, id: str) -> Agent:
        async with self._uow:
            return await self._uow.agent.find_one(id=id)

    async def settings_page(self, user_id: str) -> list:
        async with self._uow:
            server_agent = await self.get_server_agent()
            already_in_list = set()
            res: list = await self._uow.agent.user_settings_page(user_id=user_id)
            res.insert(0, server_agent)
            result = []
            for agent in res:
                if not agent.id in already_in_list:
                    result.append({
                        "id": agent.id,
                        "name": agent.name,
                        "description": agent.description,
                        "rest_url": agent.rest_url,
                        "is_connected": agent.is_connected,
                        "flag": agent.flag,
                        "secret_key": agent.secret_key
                    })
                already_in_list.add(agent.id)
            return result

    async def parents_on_settings_page(self, agent_id: str, user_id: str) -> list:
        async with self._uow:
            server_agent = await self._uow.agent.find_one(name="Server", secret_key="")
            if agent_id == server_agent.id:
                return []
            possible_parents = await self._uow.agent.possible_parent_agents(agent_id=agent_id, user_id=user_id)
            possible_parents.insert(0, server_agent)
            already_are_parents = {agent.parent_agent_id for agent in await self._uow.agent_parent_agent.filter(agent_id=agent_id) if not agent.deleted_at}
            result = []
            for pagent in possible_parents:
                result.append({
                    "id": pagent.id,
                    "name": pagent.name,
                    "is_parent": pagent.id in already_are_parents
                })
            return result

    async def set_parents_for_agent(self, parents: AgentParents, agent_id: str, user_id: str) -> list:
        async with self._uow:
            for parent, is_checked in parents.parents.items():
                agent_parent = await self._uow.agent_parent_agent.find_one(agent_id=agent_id, parent_agent_id=parent)
                if agent_parent:
                    if is_checked:
                        await self._uow.agent_parent_agent.edit_one(id=agent_parent.id, data={"deleted_at": None})
                    else:
                        await self._uow.agent_parent_agent.delete(id=agent_parent.id)
                else:
                    if is_checked:
                        self._uow.agent_parent_agent.add(AgentParentAgent(
                            agent_id=agent_id, parent_agent_id=parent).model_dump())
            await self._uow.commit()
            # agent_parent_agent = await uow.agent_parent_agent.filter()

    async def create(self, agent: Agent, user_id: str, gen_key: bool=False) -> Agent:
        async with self._uow:
            new_agent_model = Agent(
                name=agent.name,
                description=agent.description,
                rest_url=agent.rest_url,
                secret_key=get_random_bytes(32).hex() if gen_key else "",
                user_id=user_id,
            )
            new_agent = self._uow.agent.add(new_agent_model.model_dump())
            await self._uow.commit()
            return new_agent

    async def get_agents_chain(self, agent_id: str, user_id: str):
        async with self._uow:
            neighbours = await self._uow.agent_parent_agent.get_graph(user_id=user_id)
            server_agent = await self._uow.agent.find_one(name="Server", secret_key="")
        graph = {}
        for ag, pag in neighbours:
            if not ag in graph:
                graph[ag] = [pag]
            else:
                graph[ag].append(pag)
        paths = find_all_paths(graph, agent_id, server_agent.id)
        agents = []
        async with self._uow:
            for path in paths:
                agents.append([await self._uow.agent.find_one(id=ag_id) for ag_id in path])
        return agents

    async def get_parents_of_user_agent(self, agent_id: str, user_id: str):
        async with self._uow:
            return await self._uow.agent_parent_agent.get_parents_for_user_agent(agent_id=agent_id, user_id=user_id)

    async def set_connected(self, id: str):
        async with self._uow:
            await self._uow.agent.edit_one(id=id, data={"is_connected": True})
            await self._uow.commit()
