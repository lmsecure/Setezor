import datetime
import json
from typing import List
from Crypto.Random import get_random_bytes
from fastapi import HTTPException
from setezor.services.base_service import BaseService
from setezor.models import Agent, AgentInProject
from setezor.models.agent_parent_agent import AgentParentAgent
from setezor.tools.graph import find_all_paths
from setezor.schemas.agent import AgentParents, AgentUpdate


class AgentService(BaseService):
    async def get_server_agent(self):
        async with self._uow:
            return await self._uow.agent.find_one(name="Server", secret_key="")

    async def get_synthetic_agent(self):
        async with self._uow:
            return await self._uow.agent.find_one(name="Synthetic", secret_key="")

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
                    online = False
                    if agent.id == server_agent.id:
                        online = True
                    if agent.last_time_seen:
                        online = (datetime.datetime.now() - agent.last_time_seen) < datetime.timedelta(minutes=30)
                    result.append({
                        "id": agent.id,
                        "name": agent.name,
                        "description": agent.description,
                        "rest_url": agent.rest_url,
                        "is_connected": agent.is_connected,
                        "flag": agent.flag,
                        "secret_key": agent.secret_key,
                        "online": online
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

    async def update(self, agent: AgentUpdate, agent_id: str, user_id: str) -> Agent:
        async with self._uow:
            db_agent: Agent = await self._uow.agent.find_one(id=agent_id, user_id=user_id)
            if not db_agent:
                raise HTTPException(status_code=404, detail='Agent not found')
            if db_agent.is_connected and agent.rest_url:
                raise HTTPException(
                    status_code=400,
                    detail=f'Rest URL can not be changed on the connected agent. A'
                           f'gent with ID {agent_id} already connected.'
                )
            if agent.rest_url:
                db_agent.rest_url = agent.rest_url
            if agent.name:
                db_agent.name = agent.name
            if agent.description:
                db_agent.description = agent.description
            await self._uow.commit()
            return db_agent

    async def get_all_heirs(self, user_id: str, agent_id: str) -> list[dict]:
        async with self._uow:
            agent = await self._uow.agent.find_one(user_id=user_id, id=agent_id)
        if not agent:
            raise HTTPException(status_code=404)
        async with self._uow:
            return [{"id" : id, "name" : name} for id, name in await self._uow.agent.get_all_heirs(user_id=user_id, agent_id=agent_id)]

    async def delete(self, user_id: str, agent_ids: list[str]):
        async with self._uow:
            for agent_id in agent_ids:
                agent = await self._uow.agent.find_one(user_id=user_id, id=agent_id)
                if not agent:
                    raise HTTPException(status_code=404)
        async with self._uow:
            for agent_id in agent_ids:
                await self._uow.agent.edit_one(id=agent_id,
                                               data={"secret_key" : None, "is_connected": False, "rest_url" : ''})
                await self._uow.agent.delete(id=agent_id)
                await self._uow.commit()

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


    async def set_last_time_seen(self, id: str):
        async with self._uow:
            await self._uow.agent.edit_one(id=id, data={"last_time_seen": datetime.datetime.now()})
            await self._uow.commit()


    async def set_info(self, id: str, info: str):
        async with self._uow:
            await self._uow.agent.edit_one(id=id, data={"information": info})
            await self._uow.commit()

    async def user_own_agent(self, agent_id: str, user_id: str) -> Agent:
        async with self._uow:
            agent = await self._uow.agent.find_one(id=agent_id, user_id=user_id)
            if not agent:
                agent_in_project: AgentInProject = await self._uow.agent_in_project.find_one(id=agent_id)
                if agent_in_project.agent.user.id != user_id:
                    raise HTTPException(status_code=403, detail="User does not own the agent")

                agent = agent_in_project.agent

        return agent

    async def get_available_modules(self, agent_id: str, user_id: str) -> List[dict]:
        async with self._uow:
            agent = await self.user_own_agent(agent_id=agent_id, user_id=user_id)

        if not agent.is_connected:
            raise HTTPException(status_code=400, detail="Agent is not connected")
        if not agent.information:
            raise HTTPException(status_code=400, detail="Agent has not modules")
        available_tasks = [task for task in json.loads(agent.information).get("tasks", {}).items() if task[0] not in ["SelfHostedAgentInterfaces", "PushModuleTask"]]
        modules = dict()
        for task_name, task_info in available_tasks:
            if task_info.get("module_name") in modules:
                continue
            modules[task_info.get("module_name")] = {
                "task_name": task_name,
                "module_name": task_info.get("module_name"),
                "module_is_installed": task_info.get("module_is_installed"),
                "description": task_info.get("description")
            }
        return modules.values()

    async def get_uninstalled_modules(self, agent_id: str, user_id: str, modules: List[str]) -> List[str]:
        async with self._uow:
            agent = await self.user_own_agent(agent_id=agent_id, user_id=user_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        if not agent.is_connected:
            raise HTTPException(status_code=400, detail="Agent is not connected")
        if not agent.information:
            raise HTTPException(status_code=400, detail="Agent has not modules")
        installed_modules = [task.get("module_name") for task in json.loads(agent.information).get("tasks", {}).values() if task.get("module_is_installed")]
        return [module for module in modules if module and module not in installed_modules]
