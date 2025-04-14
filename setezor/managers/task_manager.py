import os
import asyncio
import base64
from typing import Callable
import json
import pickle
import aiohttp
from fastapi import HTTPException, Request, BackgroundTasks
import aiofiles
import orjson
from setezor.managers.scheduler_manager import SchedulerManager
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.models.target import Target
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.services.data_structure_service import DataStructureService
from setezor.services.scope_service import ScopeService
from setezor.tasks.base_job import BaseJob
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Task
from setezor.services import TasksService
from setezor.schemas.task import TaskPayload, \
    TaskStatus, WebSocketMessage
from setezor.tasks import get_task_by_class_name, DNSTask, WhoisTask, SdFindTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.cert_task import CertTask
from setezor.tasks.snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from setezor.spy import Spy
from setezor.managers.agent_manager import AgentManager
from setezor.managers.sender_manager import HTTPManager
from setezor.managers.cipher_manager import Cryptor
from setezor.schemas.agent import BackWardData
from setezor.settings import PATH_PREFIX
from setezor.interfaces.observer import Observer
from setezor.logger import logger


class TaskParamsPreparer:
    @classmethod
    def prepare(cls, func: Callable) -> Callable:
        async def inner(m_cls, job: BaseJob, uow: UnitOfWork, project_id: str,
                        scan_id: str, **kwargs):
            params = await cls.get_params_for_task(job=job, uow=uow,
                                                   project_id=project_id, **kwargs)
            for param in params:
                await func(cls=m_cls, job=job,
                           uow=uow,
                           project_id=project_id,
                           scan_id=scan_id,
                           **param)
        return inner

    @classmethod
    async def get_params_for_task(cls, job: BaseJob, uow: UnitOfWork,
                                  project_id: str, **kwargs):
        scope_id = kwargs.pop("scope_id", None)
        if not scope_id:
            return [kwargs]

        scope_targets = await ScopeService.get_targets(uow=uow,
                                                       project_id=project_id,
                                                       id=scope_id)
        return cls.generate_params(job=job,
                                   targets=scope_targets,
                                   **kwargs)

    @classmethod
    def generate_params(cls, job: BaseJob, targets: list[Target], **base_kwargs):
        result_params = []
        if job is NmapScanTask:
            nmap_targets = dict()
            for target in targets:
                if not target.ip:
                    continue
                if not (target.ip in nmap_targets):
                    nmap_targets[target.ip] = []
                if target.port:
                    nmap_targets[target.ip].append(target.port)
            for ip, ports in nmap_targets.items():
                if base_kwargs["targetPorts"] != "-sn":
                    result_params.append({**base_kwargs} | {"targetIP": ip})
                    continue
                if ports: # если в скоупе указаны порты для таргета, то он их и подставит
                    result_params.append({**base_kwargs} | {"targetIP": ip, 
                                                            "targetPorts": "-p " + ",".join(map(str, ports))})
        if job is MasscanScanTask:
            masscan_targets = dict()
            for target in targets:
                if not target.ip:
                    continue
                if not (target.ip in masscan_targets):
                    masscan_targets[target.ip] = []
                if target.port:
                    masscan_targets[target.ip].append(target.port)
            for ip, ports in masscan_targets.items():
                if base_kwargs["ports"]:
                    result_params.append({**base_kwargs} | {"target": ip})
                    continue
                if ports: # если в скоупе указаны порты для таргета, то он их и подставит
                    result_params.append({**base_kwargs} | {"target": ip, 
                                                            "ports": ",".join(map(str, ports))})
        return result_params

class TaskManager(Observer):

    schedulers = {}
    tasks = {}

    @classmethod  # метод сервера на создание локальной задачи
    async def create_local_job(cls, job: BaseJob,
                               uow: UnitOfWork,
                               project_id: str,
                               scan_id: str,
                               **kwargs) -> Task:
        agent_id = kwargs.pop("agent_id", None)
        task: Task = await TasksService.create(uow=uow,
                                               project_id=project_id,
                                               scan_id=scan_id,
                                               params=kwargs,
                                               agent_id=agent_id,
                                               created_by=job.__name__)

        message = WebSocketMessage(
            title="Task status", text=f"Task {task.id} {TaskStatus.created}", type="info")
        await WS_MANAGER.send_message(project_id=project_id, message=message)
        logger.debug(f"CREATED TASK {job.__qualname__}. {kwargs}")
        scheduler = cls.create_new_scheduler(job)
        new_job: BaseJob = job(
            agent_id=agent_id,
            name=f"Task {task.id}",
            scheduler=scheduler,
            uow=uow,
            task_id=task.id,
            project_id=project_id,
            scan_id=scan_id,
            **kwargs
        )
        job: BaseJob = await scheduler.spawn_job(new_job)

        return task

    @classmethod  # метод сервера на создание джобы на агенте
    @TaskParamsPreparer.prepare
    async def create_job(cls, job: BaseJob,
                         uow: UnitOfWork,
                         project_id: str,
                         scan_id: str,
                         **kwargs) -> Task:
        agent_id_in_project = kwargs.get("agent_id")
        agent_in_project = await AgentInProjectService.get_agent_in_project(uow=uow, id=agent_id_in_project)
        agent = await AgentService.get_by_id(uow=uow, id=agent_in_project.agent_id)
        if not agent.rest_url:
            message = WebSocketMessage(title="Error",
                                       text=f"Agent {agent.name} is synthetic",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=403,
                                detail=f"Agent {agent.name} is synthetic")
        if not agent.secret_key:
            message = WebSocketMessage(title="Error",
                                       text=f"Agent {
                                           agent.name} has no secret key",
                                       type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message)
            raise HTTPException(status_code=403,
                                detail=f"Agent {agent.name} has no secret key")

        agents_chain = await AgentService.get_agents_chain(uow=uow,
                                                           agent_id=agent.id,
                                                           user_id=agent.user_id)
        task: Task = await TasksService.create(uow=uow, project_id=project_id,
                                               scan_id=scan_id,
                                               params=kwargs,
                                               agent_id=agent_id_in_project,
                                               created_by=job.__name__)

        message = WebSocketMessage(title="Task status",
                                   text=f"Task {task.id} {TaskStatus.created}",
                                   type="info")
        logger.debug(f"CREATED TASK {job.__qualname__}. {kwargs}")
        await WS_MANAGER.send_message(project_id=project_id, message=message)

        task_in_agent_chain = TaskPayload(
            task_id=task.id,
            project_id=project_id,
            agent_id=agent_id_in_project,
            job_name=job.__name__,
            job_params=kwargs,
        )
        data = {
            "signal": "create_task",
            "agent_id": agent_id_in_project,
            "project_id": project_id,
            **task_in_agent_chain.model_dump()
        }
        for chain in agents_chain:
            payload = AgentManager.cipher_chain(agents_chain=chain,
                                                data=data,
                                                close_connection=True)
            body = payload["data"].encode()
            status = await HTTPManager.send_bytes(url=payload["next_agent_url"], data=body)
        return task

    @classmethod  # метод агента на создание джобы
    async def create_job_on_agent(cls, payload: TaskPayload) -> Task:
        job_cls = get_task_by_class_name(payload.job_name)
        scheduler = cls.create_new_scheduler(job_cls)
        task_id = payload.task_id
        project_id = payload.project_id
        new_job: BaseJob = job_cls(
            name=f"Task {task_id}",
            scheduler=scheduler,
            task_id=task_id,
            project_id=project_id,
            **payload.job_params
        )
        job: BaseJob = await scheduler.spawn_job(new_job)
        cls.tasks[task_id] = job
        return task_id

    @classmethod
    async def soft_stop_task(cls, uow: UnitOfWork, id: str, project_id: str) -> bool:
        task: Task = await TasksService.get(uow=uow, id=id, project_id=project_id)
        agent_in_project = await AgentInProjectService.get_agent_in_project(uow=uow, id=task.agent_id)
        agent = await AgentService.get_by_id(uow=uow, id=agent_in_project.agent_id)
        agents_chain = await AgentService.get_agents_chain(uow=uow,
                                                           agent_id=agent_in_project.agent_id,
                                                           user_id=agent.user_id)
        data = {
            "signal": "soft_stop_task",
            "id": id,
        }
        for chain in agents_chain:
            payload = AgentManager.cipher_chain(
                agents_chain=chain, data=data, close_connection=True)
            body = payload["data"].encode()
            data = await HTTPManager.send_bytes(url=payload["next_agent_url"], data=body)
            return True

    @classmethod  # метод агента на мягкое завершение таски
    async def soft_stop_task_on_agent(cls, id: str) -> str:
        task = cls.tasks.get(id)
        await task.soft_stop()
        return id

    @classmethod  # метод агента на создание шедулера
    def create_new_scheduler(cls, job: BaseJob):
        if job in cls.schedulers:
            return cls.schedulers[job]
        new_scheduler = SchedulerManager.for_job(job=job)
        cls.schedulers[job] = new_scheduler
        new_scheduler.attach(cls)
        return new_scheduler

    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/forward")
    @staticmethod  # метод агента на отправку сигнала следующему звену
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
                    raise Exception("Invalid packet")
                Spy.SECRET_KEY = payload.get("key")
                Spy.PARENT_AGENT_URLS = payload.get("parent_agents_urls")
                async with aiofiles.open(os.path.join(PATH_PREFIX, "config.json"), 'w') as file:
                    await file.write(json.dumps(payload))
                return base64.b64encode(b'OK')
            except Exception as e:
                logger.error(str(e))
                return b'You are suspicious'
        try:
            deciphered_data: bytes = Cryptor.decrypt(
                data=data, key=Spy.SECRET_KEY)
        except Exception as e:
            logger.error(str(e))
            return b''

        json_data: dict = orjson.loads(deciphered_data)
        close_connection = json_data.get("close_connection")
        if url := json_data.get("next_agent_url"):  # если мы посредник
            if close_connection:
                background_tasks.add_task(HTTPManager.send_bytes,
                                          url=url,
                                          data=json_data['data'].encode())
                logger.debug(f"Redirected payload to {url}")
                return b''
            else:
                logger.debug(f"Redirected payload to {url}")
                return await HTTPManager.send_bytes(url=url, data=json_data['data'].encode())

        signal = json_data.pop("signal", None)
        match signal:
            case "interfaces":
                return AgentManager.interfaces()
            case "create_task":
                payload = TaskPayload(**json_data)
                await TaskManager.create_job_on_agent(payload=payload)
                return b''
            case "soft_stop_task":
                task_id = json_data.get("id")
                await TaskManager.soft_stop_task_on_agent(id=task_id)
                return b''
            case _:
                return b''

    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/backward")
    @staticmethod  # метод агента на отправку данных родителю
    async def backward_request(
        data: BackWardData,
        background_tasks: BackgroundTasks = None
    ) -> bool:
        background_tasks.add_task(AgentManager.send_to_parent,
                                  data=data.model_dump())
        return True

    @classmethod
    async def send_result_to_parent_agent(cls,
                                          agent_id: str,
                                          task_id: str,
                                          result: list,
                                          raw_result: bytes = b'',
                                          raw_result_extension: str = ''):
        data = pickle.dumps(result)
        b64encoded_entities = base64.b64encode(data).decode()
        b64encoded_raw_result = base64.b64encode(raw_result).decode()
        result = {
            "signal": "result_entities",
            "task_id": task_id,
            "entities": b64encoded_entities,
            "raw_result": b64encoded_raw_result,
            "raw_result_extension": raw_result_extension,
        }
        ciphered_data = AgentManager.single_cipher(is_connected=True,
            key=Spy.SECRET_KEY, data=result).decode()
        data_for_parent_agent = {
            "sender": agent_id,
            "data": ciphered_data
        }
        for PARENT_URL in Spy.PARENT_AGENT_URLS:
            status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward",
                                        data=data_for_parent_agent)
            if status == 200:
                break

    @classmethod
    async def notify(cls, agent_id: str, data: dict):
        data_for_server = AgentManager.generate_data_for_server(agent_id=agent_id,
                                                                data=data)
        for PARENT_URL in Spy.PARENT_AGENT_URLS:
            status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward",
                                        data=data_for_server)
            if status == 200:
                break

    @classmethod
    async def task_status_changer_for_local_job(cls, data: dict, uow: UnitOfWork, project_id: str):
        await AgentManager.proceed_signal(dict_data=data, uow=uow, project_id=project_id)

    @classmethod
    async def local_writer(cls,
                           uow: UnitOfWork,
                           result: list,
                           project_id: str,
                           task_id: str,
                           scan_id: str):
        service = DataStructureService(uow=uow,
                                       result=result,
                                       project_id=project_id,
                                       scan_id=scan_id)
        await service.make_magic()
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
