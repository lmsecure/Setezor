import base64
import binascii
import copy
from typing import List
import aiohttp
import orjson
from fastapi import HTTPException
from Crypto.Random import get_random_bytes
from setezor.managers.sender_manager import HTTPManager
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.services.task_service import TasksService
from setezor.managers.cipher_manager import Cryptor
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.managers.task_result_writer import TaskResultWriter
from setezor.schemas.agent import BackWardData
from setezor.models import Agent
from setezor.logger import logger


class AgentManager:
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


    @classmethod
    async def get_interfaces_on_agent(cls, uow: UnitOfWork, project_id: str, agent_id_in_project: str, user_id: str):
        agent_in_project = await AgentInProjectService.get_agent(uow=uow, agent_id_in_project=agent_id_in_project, project_id=project_id)
        if not agent_in_project:
            raise HTTPException(status_code=404, detail="Agent not found in this project")
        agent = await AgentService.get_by_id(uow=uow, id=agent_in_project.agent_id)
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
        agents_chain: List = await AgentService.get_agents_chain(uow=uow,
                                                                 agent_id=agent.id,
                                                                 user_id=agent.user_id)
        for chain in agents_chain:
            payload = cls.cipher_chain(agents_chain=chain,
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
                deciphered_data = Cryptor.decrypt(data=b64decoded, key=agent.secret_key)
            except Exception as e:
                continue
            return orjson.loads(deciphered_data.decode())
        raise HTTPException(status_code=404, detail=f"{agent.name} is unreachable")
    

    @classmethod
    async def connect_new_agent(cls, uow: UnitOfWork, agent_id: str, user_id: str):
        agent = await AgentService.get_by_id(uow=uow, id=agent_id)
        if agent.is_connected:
            logger.error(f"{agent.name} is already connected")
            raise HTTPException(status_code=400, detail="Agent is already connected")
        if not agent.rest_url:
            logger.error(f"{agent.name} is synthetic")
            raise HTTPException(status_code=400, detail=f"{agent.name} is synthetic")
        agents_chains = await AgentService.get_agents_chain(uow=uow,
                                                            user_id=user_id,
                                                            agent_id=agent_id)
        if not agents_chains:
            logger.error(f"{agent.name} is unreachable")
            raise HTTPException(status_code=500, detail=f"{agent.name} is unreachable")
        parent_agents = await AgentService.get_parents_of_user_agent(uow=uow,
                                                                     user_id=user_id,
                                                                     agent_id=agent_id)
        data = {
            "signal": "connect",
            "key": agent.secret_key,
            "parent_agents_urls": parent_agents,
            "agent_id": agent.id
        }
        for chain in agents_chains:
            payload = cls.cipher_chain(agents_chain=chain, data=data, close_connection=False)
            next_agent_url = payload.pop("next_agent_url")
            connection_data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if isinstance(connection_data, aiohttp.client_exceptions.ClientConnectorError):
                continue
            try:
                if status != 200:
                    continue
                if connection_data["status"] == 'OK':
                    await AgentService.set_connected(uow=uow, id=agent_id)
                    return
            except binascii.Error:
                continue
        raise HTTPException(status_code=500, detail=f"{agent.name} has not been connected")

    @classmethod
    async def decipher_data_from_project_agent(cls, uow: UnitOfWork, data: BackWardData):
        agent_in_project = await AgentInProjectService.get_agent_in_project(uow=uow, id=data.sender)
        if not agent_in_project:
            return
        agent: Agent = await AgentService.get_by_id(uow=uow, id=agent_in_project.agent_id)
        ciphered_payload = data.data.encode()
        b64decoded = base64.b64decode(ciphered_payload)
        deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                             key=agent.secret_key)
        dict_data = orjson.loads(deciphered_payload)
        project_id = agent_in_project.project_id
        await cls.proceed_signal(dict_data=dict_data, uow=uow, project_id=project_id)

    @classmethod
    async def proceed_signal(cls, dict_data: dict, uow: UnitOfWork, project_id: str):
        copy_of_dict = copy.deepcopy(dict_data)
        signal = copy_of_dict.pop("signal", None)
        match signal:
            case "notify":
                payload = WebSocketMessage(**copy_of_dict)
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
            case "task_status":
                await TasksService.set_status(uow=uow,
                                              id=copy_of_dict["task_id"],
                                              status=copy_of_dict["status"],
                                              traceback=copy_of_dict["traceback"])
                payload = WebSocketMessage(
                    title="Task status",
                    text=f"Task with task_id = {copy_of_dict["task_id"]} {
                        copy_of_dict["status"]}. {copy_of_dict["traceback"]}",
                    type=copy_of_dict["type"]
                )
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
            case "result_entities":
                task_id = copy_of_dict["task_id"]
                task_data = copy_of_dict["result"]
                if (raw_result := task_data.get("raw_result")) and (extension := copy_of_dict.get("raw_result_extension")):
                    await TaskResultWriter.write_raw_result(task_id=task_id,
                                                            data=raw_result,
                                                            extension=extension,
                                                            uow=uow)
                await TaskResultWriter.write_result(task_id=task_id,
                                                    data=task_data,
                                                    uow=uow)
                await TasksService.set_status(uow=uow,
                                              id=task_id,
                                              status=TaskStatus.finished)
                payload = WebSocketMessage(
                    title="Task status",
                    text=f"Task with {task_id=} {TaskStatus.finished}",
                    type="info"
                )
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
