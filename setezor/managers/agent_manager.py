import base64
import copy
from typing import List
import aiohttp
import orjson
from fastapi import HTTPException
from Crypto.Random import get_random_bytes
from setezor.managers.sender_manager import HTTPManager
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.services.agent_service import AgentService
from setezor.services.task_service import TasksService
from setezor.spy import Spy
from setezor.tools.ip_tools import get_interfaces
from setezor.managers.cipher_manager import Cryptor
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.managers.task_result_writer import TaskResultWriter
from setezor.schemas.agent import BackWardData
from setezor.models import Agent
from setezor.logger import logger


class AgentManager:
    @classmethod
    def single_cipher(cls, key: str, data: dict):
        initial_data = orjson.dumps(data)
        if not key:
            return base64.b64encode(initial_data)
        return base64.b64encode(Cryptor.encrypt(initial_data, key))

    @classmethod
    def cipher_chain(cls, agents_chain: list[Agent], data: dict, close_connection: bool):
        for agent in agents_chain:
            ciphered_payload_by_current_agent = cls.single_cipher(key=agent.secret_key,
                                                                  data=data)
            data = {
                "next_agent_url": f"{agent.rest_url}/api/v1/agents/forward",
                "close_connection": close_connection,
                "agent_id": agent.id,
                "project_id": agent.project_id,
                "data": ciphered_payload_by_current_agent.decode()
            }
        return data

    @classmethod
    def generate_data_for_server(cls, agent_id: str, data: dict):
        ciphered_payload_by_current_agent = cls.single_cipher(key=Spy.SECRET_KEY,
                                                              data=data)
        return {
            "sender": agent_id,
            "data": ciphered_payload_by_current_agent.decode()
        }

    @classmethod
    async def get_interfaces_on_agent(cls, uow: UnitOfWork, project_id: str, agent_id: str):
        agent = await AgentService.get(uow=uow, id=agent_id, project_id=project_id)
        if not agent.rest_url:
            return []
        if not agent.secret_key:
            message = WebSocketMessage(title="Error",
                                       text=f"{
                                           agent.name} is not connected yet",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        agents_chain: List = await AgentService.get_agents_chain(uow=uow,
                                                                 agent_id=agent_id,
                                                                 project_id=project_id)
        payload = cls.cipher_chain(agents_chain=agents_chain,
                                            data={
                                                "signal": "interfaces",
                                                "agent_id": agent.id
                                            },
                                            close_connection=False)
        body = payload["data"].encode()
        data = await HTTPManager.send_bytes(url=payload["next_agent_url"], data=body)
        if isinstance(data, aiohttp.client_exceptions.ClientConnectorError):
            message = WebSocketMessage(title="Error",
                                       text=f"{agent.name} is unreachable",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        b64decoded = base64.b64decode(data)
        try:
            deciphered_data = Cryptor.decrypt(data=b64decoded, key=agent.secret_key)
        except Exception as e:
            logger.error(str(e))
            message = WebSocketMessage(title="Error",
                                       text=f"Error while decrypting payload",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        return orjson.loads(deciphered_data.decode())

    @classmethod
    def interfaces(cls):
        interfaces = [iface.model_dump() for iface in get_interfaces()]
        initial_data = orjson.dumps(interfaces)
        return base64.b64encode(Cryptor.encrypt(initial_data, Spy.SECRET_KEY))

    @classmethod
    async def connect_new_agent(cls, uow: UnitOfWork, project_id: str, agent_id: str):
        agent = await AgentService.get(uow=uow, id=agent_id, project_id=project_id)
        if agent.secret_key:
            logger.error(f"{agent.name} is already connected")
            message = WebSocketMessage(title="Error",
                                       text=f"{agent.name} is already connected",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id,
                                          message=message)
            raise HTTPException(status_code=400)
        if not agent.rest_url:
            logger.error(f"{agent.name} is synthetic")
            message = WebSocketMessage(title="Error",
                                       text=f"{agent.name} is synthetic",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=400)
        new_key = get_random_bytes(32).hex()
        agents_chain = await AgentService.get_agents_chain(uow=uow,
                                                           agent_id=agent_id,
                                                           project_id=project_id)
        parent_agent = await AgentService.get(uow=uow,
                                              id=agent.parent_agent_id,
                                              project_id=project_id)
        data = {
            "signal": "connect",
            "project_id": project_id,
            "agent_id": agent.id,
            "key": new_key,
            "parent_agent_url": parent_agent.rest_url
        }
        payload = cls.cipher_chain(
            agents_chain=agents_chain, data=data, close_connection=False)
        body = payload["data"].encode()

        connection_data = await HTTPManager.send_bytes(url=payload["next_agent_url"], data=body)
        if base64.b64decode(connection_data.decode()) == b'OK':
            message = WebSocketMessage(title="Info",
                                       text=f"{
                                           agent.name} was successfully connected",
                                       type="success")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            await AgentService.set_key(uow=uow, id=agent_id, key=new_key)

    @classmethod
    async def decipher_data_from_agent(cls, uow: UnitOfWork, data: BackWardData):
        agent: Agent = await AgentService.get_by_id(uow=uow, id=data.sender)
        if not agent:
            return
        ciphered_payload = data.data.encode()
        b64decoded = base64.b64decode(ciphered_payload)
        deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                             key=agent.secret_key)
        dict_data = orjson.loads(deciphered_payload)
        project_id = agent.project_id
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
                                              project_id=copy_of_dict)
                payload = WebSocketMessage(
                    title="Task status",
                    text=f"Task with task_id = {copy_of_dict["task_id"]} {
                        copy_of_dict["status"]}. {copy_of_dict["traceback"]}",
                    type=copy_of_dict["type"]
                )
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
            case "result_entities":
                b64decoded_entities = base64.b64decode(
                    copy_of_dict["entities"].encode())
                task_id = copy_of_dict["task_id"]
                if raw_result := copy_of_dict.get("raw_result"):
                    extension = copy_of_dict.get("raw_result_extension")
                    raw_data = base64.b64decode(raw_result.encode())
                    await TaskResultWriter.write_raw_result(task_id=task_id,
                                                            data=raw_data,
                                                            extension=extension,
                                                            uow=uow)
                await TaskResultWriter.write_result(task_id=task_id,
                                                    data=b64decoded_entities,
                                                    uow=uow)
                await TasksService.set_status(uow=uow,
                                              id=task_id,
                                              status=TaskStatus.finished,
                                              project_id=project_id)
                payload = WebSocketMessage(
                    title="Task status",
                    text=f"Task with {task_id=} {TaskStatus.finished}",
                    type="info"
                )
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
