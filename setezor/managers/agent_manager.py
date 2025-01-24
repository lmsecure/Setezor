import base64
import json
import os
from typing import List
from Crypto.Random import get_random_bytes
import orjson
import aiohttp
import aiofiles
from fastapi import BackgroundTasks, Request, HTTPException
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.models.agent import Agent
from setezor.schemas.agent import BackWardData
from setezor.schemas.task import TaskPayload, WebSocketMessage, WebSocketMessageForProject
from setezor.spy import Spy
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.tools.ip_tools import get_interfaces
from setezor.managers import cipher_manager as CM, task_manager as TM
from setezor.setezor import path_prefix

class AgentManager:
    @classmethod
    async def get_agents_chain(cls, uow: UnitOfWork, agent_id: str, project_id: str):
        agents_chain_urls = []
        async with uow:
            while True:
                agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
                if not agent.parent_agent_id: break
                agent_id = agent.parent_agent_id
                agents_chain_urls.append(agent)
        return agents_chain_urls
    
    @classmethod
    def single_cipher(cls, key: str, data: dict):
        initial_data = orjson.dumps(data)
        if not key:
            return base64.b64encode(initial_data)
        return base64.b64encode(CM.CipherManager.cipher(initial_data, key))

    @classmethod
    def cipherPayload(cls, agents_chain, data: dict, close_connection: bool):
        for agent in agents_chain:
            ciphered_payload_by_current_agent = cls.single_cipher(key=agent.secret_key, data=data)
            data = {
                "next_agent_url": f"{agent.rest_url}/api/v1/agents/forward",
                "close_connection": close_connection,
                "agent_id": agent.id,
                "project_id": agent.project_id,
                "data": ciphered_payload_by_current_agent.decode()
            }
        return data
    
    @classmethod
    async def decipher_data_from_agent(cls, uow: UnitOfWork, data: BackWardData):
        async with uow:
            agent: Agent = await uow.agent.find_one(id=data.sender)
        if not agent: return
        ciphered_payload = data.data.encode()
        b64decoded = base64.b64decode(ciphered_payload)
        deciphered_payload = CM.CipherManager.decipher(data=b64decoded, key=agent.secret_key)
        dict_data = orjson.loads(deciphered_payload)
        signal = dict_data.pop("signal", None)
        match signal:
            case "notify":
                project_id = agent.project_id
                payload = WebSocketMessage(**dict_data)
                await WS_MANAGER.send_message(project_id=project_id, message=payload)
            case "result_entities":
                b64decoded_entities = base64.b64decode(dict_data["entities"].encode())
                task_id = dict_data["task_id"]
                await TM.TaskManager.write_result(task_id=task_id, data=b64decoded_entities, uow=uow)


    @classmethod
    async def connect_new_agent(cls, uow: UnitOfWork, project_id: str, agent_id: str):
        async with uow:
            agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
            if agent.secret_key:
                message = WebSocketMessage(title="Error", text=f"{agent.name} is already connected",type="error")
                await WS_MANAGER.send_message(project_id=project_id, message=message)
                raise HTTPException(status_code=400)
            if not agent.rest_url:
                message = WebSocketMessage(title="Error", text=f"{agent.name} is synthetic",type="error")
                await WS_MANAGER.send_message(project_id=project_id, message=message)
                raise HTTPException(status_code=400)
            new_key = get_random_bytes(32).hex()
            agents_chain = await cls.get_agents_chain(uow=uow, agent_id=agent_id, project_id=project_id)
            parent_agent = await uow.agent.find_one(id=agent.parent_agent_id)
            data = {
                "signal": "connect",
                "project_id": project_id,
                "agent_id": agent.id,
                "key": new_key,
                "parent_agent_url": parent_agent.rest_url
            }
            payload = cls.cipherPayload(agents_chain=agents_chain, data=data, close_connection=False)
            body = payload["data"].encode()
            
            agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
            agent.secret_key = new_key
            data = await cls.send_bytes(url=payload["next_agent_url"], data=body)
            if base64.b64decode(data.decode()) == b'OK':
                message = WebSocketMessage(title="Info", text=f"{agent.name} was successfully connected",type="success")
                await WS_MANAGER.send_message(project_id=project_id, message=message)
                await uow.commit()
            



    @classmethod
    async def get_interfaces_on_agent(cls, uow: UnitOfWork, project_id:str, agent_id: str):
        async with uow:
            agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
        if not agent.rest_url:
            return []
        if not agent.secret_key:
            message = WebSocketMessage(title="Error", text=f"{agent.name} is not connected yet",type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        agents_chain: List = await cls.get_agents_chain(uow=uow, agent_id=agent_id, project_id=project_id)
        payload = cls.cipherPayload(agents_chain=agents_chain, 
                                    data={
                                        "signal":"interfaces",
                                        "agent_id": agent.id
                                        }, 
                                    close_connection=False)
        body = payload["data"].encode()
        data = await cls.send_bytes(url=payload["next_agent_url"], data=body)
        if isinstance(data, aiohttp.client_exceptions.ClientConnectorError):
            message = WebSocketMessage(title="Error", text=f"{agent.name} is unreachable",type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=404)
        b64decoded = base64.b64decode(data)
        deciphered_data = CM.CipherManager.decipher(data=b64decoded, key=agent.secret_key)
        return orjson.loads(deciphered_data.decode())

    @classmethod
    def generate_websocket_message(cls, agent_id:str, message: WebSocketMessageForProject):
        data = {
            "signal": "notify",
            **message.model_dump()
        }
        ciphered_payload_by_current_agent = AgentManager.single_cipher(key=Spy.SECRET_KEY, data=data)
        return {
            "sender": agent_id,
            "data": ciphered_payload_by_current_agent.decode()
        }
    
    
    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/forward")
    @staticmethod # метод агента на отправку сигнала следующему звену
    async def forward_request(
        request: Request, 
        background_tasks: BackgroundTasks = None
    ) -> bytes:
        body: bytes = await request.body()
        data: bytes = base64.b64decode(body)
        if not Spy.SECRET_KEY:
            try:
                data = data.decode()
                payload = orjson.loads(data)
                if not payload.pop("signal", None) == "connect":
                    raise Exception
                Spy.SECRET_KEY = payload.get("key")
                Spy.PARENT_AGENT_URL = payload.get("parent_agent_url")
                async with aiofiles.open(os.path.join(path_prefix, "config.json"), 'w') as file:
                    await file.write(json.dumps(payload))
                return base64.b64encode(b'OK')
            except:
                return b'You are suspicious'

        deciphered_data: bytes = CM.CipherManager.decipher(data=data, key=Spy.SECRET_KEY)
        json_data: dict = orjson.loads(deciphered_data)
        close_connection = json_data.get("close_connection")
        if url := json_data.get("next_agent_url"): # если мы посредник
            if close_connection:
                background_tasks.add_task(AgentManager.send_bytes, url=url, data=json_data['data'].encode())
                return b''
            else:
                return await AgentManager.send_bytes(url=url, data=json_data['data'].encode())
        
        signal = json_data.pop("signal", None)
        match signal:
            case "interfaces":
                interfaces = [iface.model_dump() for iface in get_interfaces()]
                initial_data = orjson.dumps(interfaces)
                return base64.b64encode(CM.CipherManager.cipher(initial_data, Spy.SECRET_KEY))
            case "create_task":
                payload = TaskPayload(**json_data)
                await TM.TaskManager.create_job_on_agent(payload=payload)
                return b''
            case "start_task":
                task_id = json_data.get("id")
                await TM.TaskManager.start_job_on_agent(id=task_id)
            case "soft_stop_task":
                task_id = json_data.get("id")
                await TM.TaskManager.soft_stop_task_on_agent(id=task_id)
            case _:
                return b''
    
    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/backward")
    @staticmethod # метод агента на отправку данных родителю
    async def send_to_parent_agent(
        data: BackWardData,
        background_tasks: BackgroundTasks = None
    ) -> bool:
        background_tasks.add_task(AgentManager.send_request, url=f"{Spy.PARENT_AGENT_URL}/api/v1/agents/backward", data=data.model_dump())
        return True

        
    @classmethod # метод агента на отправку результата на предыдущего агента
    async def send_bytes(cls, url: str, data: bytes):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data, ssl=False) as resp:
                    return await resp.read()
            except aiohttp.client_exceptions.ClientConnectorError as e:
                return e

    @classmethod # метод сервера и агента на отправку следующему звену
    async def send_request(cls, url: str, data: dict | list[dict]):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, ssl=False) as resp:
                return resp.status