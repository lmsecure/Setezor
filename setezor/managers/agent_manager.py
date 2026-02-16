import base64
import binascii
from typing import Annotated, List
import aiohttp
import orjson
from fastapi import Depends, HTTPException

from setezor.network_structures import InterfaceStruct
from setezor.services.agent_interface_serivce import AgentInterfaceService
from setezor.tools.sender_manager import HTTPManager
from setezor.models.base import generate_unique_id
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.schemas.task import WebSocketMessage
from setezor.schemas.agent import InterfaceOfAgent
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.tools.cipher_manager import Cryptor
from setezor.tools.ip_tools import get_network
from setezor.models import Agent, MAC, Object, ASN, IP, Domain, DNS, AgentInterface, Network
from setezor.db.entities import DNSTypes
from setezor.logger import logger


class AgentManager:
    def __init__(
        self,
        agent_service: AgentService,
        agent_in_project_service: AgentInProjectService,
        agent_interface_service: AgentInterfaceService,
    ):
        self.__agent_service: AgentService = agent_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service
        self.__agent_interface_service: AgentInterfaceService = agent_interface_service

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

    async def get_interfaces_on_agent(self, agent_id: str, user_id: str):
        agent = await self.__agent_service.get_by_id(id=agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail="Agent not found")
        if not agent.rest_url:
            return []
        if not agent.secret_key:
            message = WebSocketMessage(title="Error",
                                       text=f"{
                                           agent.name} is not connected yet",
                                       type="error",
                                       user_id=user_id,
                                       command="notify_user")
            await WS_MANAGER.send_message(entity_id=user_id, message=message)
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
                    data=b64decoded,
                    key=agent.secret_key
                )
                remote_interfaces = [
                    InterfaceStruct(**item)
                    for item in orjson.loads(deciphered_data.decode())
                ]
                remote_interfaces_names = [interface.name for interface in remote_interfaces]
                interfaces = await self.__agent_interface_service.find_by_names(agent_id=agent.id, interfaces=remote_interfaces_names)
                interface_names = [interface.name for interface in interfaces]
                for interface in remote_interfaces:
                    if interface.name in interface_names:
                        interface.is_already_enabled = True

            except Exception:
                continue
            return remote_interfaces
        raise HTTPException(
            status_code=404,
            detail=f"{agent.name} is unreachable"
        )

    async def save_interfaces(self, user_id: str, agent_id: str, interfaces: List[InterfaceOfAgent]):
        async with self.__agent_service._uow:
            agent: Agent = await self.__agent_service._uow.agent.find_one(id=agent_id)
            if not agent:
                raise HTTPException(
                    status_code=404, detail="Agent not found")
            enabled_interfaces: set[str] = set((f"{interface.ip}_{interface.name}") for interface in await self.__agent_service._uow.agent_interface.filter(agent_id=agent.id))
            for interface in interfaces:
                if f"{interface.ip}_{interface.name}" in enabled_interfaces:
                    continue
                interface_obj = AgentInterface(
                    id=generate_unique_id(),
                    agent_id = agent.id,
                    ip = interface.ip,
                    mac = interface.mac,
                    name = interface.name
                )
                self.__agent_service._uow.agent_interface.add(interface_obj.model_dump())
                agents_in_projects = await self.__agent_service._uow.agent_in_project.filter(agent_id = agent_id)
                for agent_in_project in agents_in_projects:
                    new_obj = Object(id=generate_unique_id(), project_id=agent_in_project.project_id, agent_id=agent_in_project.id)
                    self.__agent_service._uow.object.add(new_obj.model_dump())
                    mac_obj = MAC(id=generate_unique_id(), mac=interface_obj.mac, object_id=new_obj.id, name=interface_obj.name, project_id=agent_in_project.project_id)
                    self.__agent_service._uow.mac.add(mac_obj.model_dump())
                    asn_obj =ASN(id=generate_unique_id(), project_id=agent_in_project.project_id)
                    self.__agent_service._uow.asn.add(asn_obj.model_dump())
                    network_obj = Network(id=generate_unique_id(), asn_id=asn_obj.id, project_id=agent_in_project.project_id)
                    self.__agent_service._uow.network.add(network_obj.model_dump())
                    ip_obj = IP(id=generate_unique_id(), ip=interface_obj.ip, interface_id=interface_obj.id, project_id=agent_in_project.project_id, mac_id=mac_obj.id, network_id=network_obj.id)
                    self.__agent_service._uow.ip.add(ip_obj.model_dump())
            await self.__agent_service._uow.commit()
            message = WebSocketMessage(
                title="Info", text=f"Saved interfaces for {agent.name}", type="info")
            await WS_MANAGER.send_message(entity_id=user_id, message=message)
        return True

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
            msg_details = f"Parent agents have not been set for {agent.name} agent"
            logger.error(msg_details)
            raise HTTPException(
                status_code=400, detail=msg_details)
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
            connection_data, status = await HTTPManager.send_json(url=next_agent_url, data=payload, timeout=10.0)
            if isinstance(connection_data, aiohttp.client_exceptions.ClientConnectorError):
                continue
            try:
                if status != 200 or not connection_data.get("status"):
                    continue
                if connection_data["status"] == 'OK':
                    await self.__agent_service.set_connected(id=agent_id)
                    return
            except binascii.Error:
                continue
        raise HTTPException(
            status_code=400, detail=f"{agent.name} has not been connected"
        )

    async def is_agent_exist(self, agent_id: str) -> bool:
        return await self.__agent_service.get_by_id(id=agent_id) is not None

    @classmethod
    def new_instance(
        cls,
        agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
        agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
        agent_interface_service: Annotated[AgentInterfaceService, Depends(AgentInterfaceService.new_instance)],
    ):
        return cls(
            agent_service=agent_service,
            agent_in_project_service=agent_in_project_service,
            agent_interface_service=agent_interface_service,
        )
