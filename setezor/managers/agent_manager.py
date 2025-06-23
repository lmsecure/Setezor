import base64
import binascii
from typing import Annotated, List
import aiohttp
import orjson
from fastapi import Depends, HTTPException
from setezor.tools.sender_manager import HTTPManager
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.schemas.task import WebSocketMessage
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.tools.cipher_manager import Cryptor
from setezor.models import Agent
from setezor.logger import logger


class AgentManager:
    def __init__(
        self,
        agent_service: AgentService,
        agent_in_project_service: AgentInProjectService,
    ):
        self.__agent_service: AgentService = agent_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service

    @classmethod
    def single_cipher(cls, key: str, is_connected: bool, data: dict):
        initial_data = orjson.dumps(data)
        if not is_connected:
            return base64.b64encode(initial_data)
        return base64.b64encode(Cryptor.encrypt(initial_data, key))

    @classmethod
    def cipher_chain(cls, agents_chain: list[Agent], data: dict, close_connection: bool):
        for agent in agents_chain:
            ciphered_payload_by_current_agent = cls.single_cipher(key=agent.secret_key,
                                                                  is_connected=agent.is_connected,
                                                                  data=data)
            data = {
                "next_agent_url": f"{agent.rest_url}/api/v1/agents/forward",
                "close_connection": close_connection,
                "data": ciphered_payload_by_current_agent.decode()
            }
        return data

    async def get_interfaces_on_agent(self, project_id: str, agent_id_in_project: str, user_id: str):
        agent_in_project = await self.__agent_in_project_service.get_agent(agent_id_in_project=agent_id_in_project, project_id=project_id)
        if not agent_in_project:
            raise HTTPException(
                status_code=404, detail="Agent not found in this project")
        agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        if not agent.rest_url:
            return []
        if not agent.secret_key:
            message = WebSocketMessage(title="Error",
                                       text=f"{
                                           agent.name} is not connected yet",
                                       type="error",
                                       user_id=user_id,
                                       command="notify_user")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        agents_chain: List = await self.__agent_service.get_agents_chain(agent_id=agent.id,
                                                                         user_id=agent.user_id)
        for chain in agents_chain:
            payload = self.cipher_chain(agents_chain=chain,
                                        data={
                                            "signal": "interfaces",
                                            "agent_id": agent.id
                                        },
                                        close_connection=False)
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if isinstance(data, aiohttp.client_exceptions.ClientConnectorError):
                continue
            b64decoded = base64.b64decode(data["data"])
            try:
                deciphered_data = Cryptor.decrypt(
                    data=b64decoded, key=agent.secret_key)
            except Exception as e:
                continue
            return orjson.loads(deciphered_data.decode())
        raise HTTPException(
            status_code=404, detail=f"{agent.name} is unreachable")

    async def connect_new_agent(self, agent_id: str, user_id: str):
        agent = await self.__agent_service.get_by_id(id=agent_id)
        if agent.is_connected:
            logger.error(f"{agent.name} is already connected")
            raise HTTPException(
                status_code=400, detail="Agent is already connected")
        if not agent.rest_url:
            logger.error(f"{agent.name} is synthetic")
            raise HTTPException(
                status_code=400, detail=f"{agent.name} is synthetic")
        agents_chains = await self.__agent_service.get_agents_chain(user_id=user_id,
                                                                    agent_id=agent_id)
        if not agents_chains:
            logger.error(f"{agent.name} is unreachable")
            raise HTTPException(
                status_code=500, detail=f"{agent.name} is unreachable")
        parent_agents = await self.__agent_service.get_parents_of_user_agent(user_id=user_id,
                                                                             agent_id=agent_id)
        data = {
            "signal": "connect",
            "key": agent.secret_key,
            "parent_agents_urls": parent_agents,
            "agent_id": agent.id
        }
        for chain in agents_chains:
            payload = self.cipher_chain(
                agents_chain=chain, data=data, close_connection=False)
            next_agent_url = payload.pop("next_agent_url")
            connection_data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if isinstance(connection_data, aiohttp.client_exceptions.ClientConnectorError):
                continue
            try:
                if status != 200:
                    continue
                if connection_data["status"] == 'OK':
                    await self.__agent_service.set_connected(id=agent_id)
                    return
            except binascii.Error:
                continue
        raise HTTPException(
            status_code=500, detail=f"{agent.name} has not been connected")


    @classmethod
    def new_instance(
        cls,
        agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
        agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
    ):
        return cls(
            agent_service=agent_service,
            agent_in_project_service=agent_in_project_service,
        )
