import base64
import copy
import datetime
import json
import os
from typing import Annotated, Callable
import aiofiles
from fastapi import Depends, HTTPException
import orjson
from setezor.managers.project_manager.files import ProjectFolders
from setezor.models.agent import Agent
from setezor.schemas.agent import BackWardData
from setezor.tools.cipher_manager import Cryptor
from setezor.tools.scheduler_manager import SchedulerManager
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.models.target import Target
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.data_writer.data_structure_service import DataStructureService
from setezor.services.scope_service import ScopeService
from setezor.tasks import get_folder_for_task, get_restructor_for_task, get_task_by_class_name
from setezor.tasks.base_job import BaseJob
from setezor.tasks.speed_test_task import SpeedTestServerTask, SpeedTestClientTask
from setezor.models import Task
from setezor.services import TasksService
from setezor.schemas.task import TaskPayload, \
    TaskStatus, WebSocketMessage
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.managers.agent_manager import AgentManager
from setezor.tools.sender_manager import HTTPManager
from setezor.logger import logger


class TaskParamsPreparer:
    @classmethod
    def prepare(cls, func: Callable) -> Callable:
        async def inner(self, job: BaseJob, project_id: str,
                        scan_id: str, **kwargs):
            params = await cls.get_params_for_task(tm=self, job=job,
                                                   project_id=project_id, **kwargs)
            for param in params:
                await func(self, job=job,
                           project_id=project_id,
                           scan_id=scan_id,
                           **param)
        return inner

    @classmethod
    async def get_params_for_task(cls, tm: "TaskManager", job: BaseJob,
                                  project_id: str, **kwargs):
        scope_id = kwargs.pop("scope_id", None)
        if not scope_id:
            return [kwargs]

        scope_targets = await tm.scope_service.get_targets(project_id=project_id,
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
                if ports:  # если в скоупе указаны порты для таргета, то он их и подставит
                    result_params.append({**base_kwargs} | {"targetIP": ip,
                                                            "targetPorts": "-p " + ",".join(map(str, ports))})
                    continue
                result_params.append({**base_kwargs} | {"targetIP": ip})
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
                if ports:  # если в скоупе указаны порты для таргета, то он их и подставит
                    result_params.append({**base_kwargs} | {"target": ip,
                                                            "ports": ",".join(map(str, ports))})
                    continue
                result_params.append({**base_kwargs} | {"target": ip})
        return result_params


class TaskManager:

    schedulers = {}
    tasks = {}

    def __init__(
        self,
        tasks_service: TasksService,
        agent_in_project_service: AgentInProjectService,
        agent_service: AgentService,
        data_structure_service: DataStructureService,
        scope_service: ScopeService,
        agent_manager: AgentManager,
    ):
        self.__tasks_service: TasksService = tasks_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service
        self.__agent_service: AgentService = agent_service
        self.__data_structure_service: DataStructureService = data_structure_service
        self.__scope_service: ScopeService = scope_service
        self.__agent_manager: AgentManager = agent_manager

    @property
    def scope_service(self):
        return self.__scope_service

    # метод сервера на создание локальной задачи
    async def create_local_job(self,
                               job: BaseJob,
                               project_id: str,
                               scan_id: str,
                               **kwargs) -> Task:
        def safe_json(obj):
            try:
                json.dumps(obj)
                return True
            except TypeError:
                return False

        safe_params = {k: v for k, v in kwargs.items() if safe_json(v)}
        
        agent_id = kwargs.pop("agent_id", None)
        task: Task = await self.__tasks_service.create(project_id=project_id,
                                                       scan_id=scan_id,
                                                       params=safe_params,
                                                       agent_id=agent_id,
                                                       created_by=job.__name__)

        message = WebSocketMessage(
            title="Task status", text=f"Task {task.id} {TaskStatus.created}", type="info")
        await WS_MANAGER.send_message(project_id=project_id, message=message)
        logger.debug(f"CREATED TASK {job.__qualname__}. {safe_params}")
        scheduler = self.create_new_scheduler(job)
        new_job: BaseJob = job(
            task_manager=self,
            agent_id=agent_id,
            name=f"Task {task.id}",
            scheduler=scheduler,
            task_id=task.id,
            project_id=project_id,
            scan_id=scan_id,
            **kwargs
        )
        job: BaseJob = await scheduler.spawn_job(new_job)

        return task

    # метод сервера на создание джобы на агенте
    @TaskParamsPreparer.prepare
    async def create_job(self, job: BaseJob,
                         project_id: str,
                         scan_id: str,
                         **kwargs) -> Task:
        agent_id_in_project = kwargs.get("agent_id")
        agent_in_project = await self.__agent_in_project_service.get_agent_in_project(id=agent_id_in_project)
        agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
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

        agents_chain = await self.__agent_service.get_agents_chain(agent_id=agent.id,
                                                                   user_id=agent.user_id)
        task: Task = await self.__tasks_service.create(project_id=project_id,
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
            payload = self.__agent_manager.cipher_chain(agents_chain=chain,
                                                        data=data,
                                                        close_connection=True)
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if status == 200:
                break
        return

    async def soft_stop_task(self, id: str, project_id: str) -> bool:
        task: Task = await self.__tasks_service.get(id=id, project_id=project_id)
        agent_in_project = await self.__agent_in_project_service.get_agent_in_project(id=task.agent_id)
        agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        agents_chain = await self.__agent_service.get_agents_chain(agent_id=agent_in_project.agent_id,
                                                                   user_id=agent.user_id)
        data = {
            "signal": "soft_stop_task",
            "id": id,
        }
        for chain in agents_chain:
            payload = self.__agent_manager.cipher_chain(
                agents_chain=chain, data=data, close_connection=True)
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if status == 200:
                break
        return True

    async def delete_task(self, id: str, project_id: str) -> bool:
        task: Task = await self.__tasks_service.get(id=id, project_id=project_id)
        if not task:
            return False
        await self.__tasks_service.set_status(id=id, status=TaskStatus.failed, traceback="User canceled the task")
        return True

    # метод агента на создание шедулера
    def create_new_scheduler(self, job: BaseJob):
        if job in self.schedulers:
            return self.schedulers[job]
        new_scheduler = SchedulerManager.for_job(job=job)
        self.schedulers[job] = new_scheduler
        return new_scheduler

    async def task_status_changer_for_local_job(self, data: dict, project_id: str):
        await self.proceed_signal(dict_data=data, project_id=project_id)
        if data.get("signal") == "task_status" and data.get("status") == TaskStatus.failed:
            self.delete_task(task_id=data.get("task_id"))

    async def local_writer(self,
                           result: list,
                           project_id: str,
                           task_id: str,
                           scan_id: str):
        await self.__data_structure_service.make_magic(result=result,
                                                       project_id=project_id,
                                                       scan_id=scan_id)
        await self.__tasks_service.set_status(id=task_id,
                                              status=TaskStatus.finished)
        payload = WebSocketMessage(
            title="Task status",
            text=f"Task with {task_id=} {TaskStatus.finished}",
            type="info"
        )
        await WS_MANAGER.send_message(project_id=project_id,
                                      message=payload)
        self.delete_task(task_id=task_id)

    @classmethod
    def delete_task(cls, task_id: str):
        cls.tasks.pop(task_id, None)

    @classmethod
    def new_instance(
        cls,
        tasks_service: Annotated[TasksService, Depends(TasksService.new_instance)],
        agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
        agent_service: Annotated[AgentService, Depends(AgentService.new_instance)],
        data_structure_service: Annotated[DataStructureService, Depends(DataStructureService.new_instance)],
        scope_service: Annotated[ScopeService, Depends(ScopeService.new_instance)],
        agent_manager: Annotated[AgentManager, Depends(AgentManager.new_instance)],
    ):
        return cls(
            tasks_service=tasks_service,
            agent_in_project_service=agent_in_project_service,
            agent_service=agent_service,
            data_structure_service=data_structure_service,
            scope_service=scope_service,
            agent_manager=agent_manager,
        )


    async def autostart_speed_test_client(self, task_id: str):
        task = await self.__tasks_service.get_by_id(id=task_id)
        if not (get_task_by_class_name(task.created_by) is SpeedTestServerTask):
            return
        task_params = json.loads(task.params)
        task_params["agent_id"] = task_params.get("agent_id_from")
        await self.create_job(job=SpeedTestClientTask,
                              project_id=task.project_id,
                              scan_id=task.scan_id,
                              **task_params)


    async def decipher_data_from_project_agent(self, data: BackWardData):
        agent_in_project = await self.__agent_in_project_service.get_agent_in_project(id=data.sender)
        if not agent_in_project:
            return
        agent: Agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        ciphered_payload = data.data.encode()
        b64decoded = base64.b64decode(ciphered_payload)
        deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                             key=agent.secret_key)
        dict_data = orjson.loads(deciphered_payload)
        project_id = agent_in_project.project_id
        await self.proceed_signal(dict_data=dict_data, project_id=project_id)

    async def proceed_signal(self, dict_data: dict, project_id: str):
        from setezor.managers.task_manager import TaskManager
        copy_of_dict = copy.deepcopy(dict_data)
        signal = copy_of_dict.pop("signal", None)
        match signal:
            case "notify":
                payload = WebSocketMessage(**copy_of_dict)
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)
            case "task_status":
                await self.__tasks_service.set_status(id=copy_of_dict["task_id"],
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
                ##################################
                if copy_of_dict["status"] == TaskStatus.started:
                    await self.autostart_speed_test_client(task_id=copy_of_dict["task_id"])
                ##################################

            case "result_entities":
                task_id = copy_of_dict["task_id"]
                task_data = copy_of_dict["result"]
                if (raw_result := task_data.get("raw_result")) and (extension := copy_of_dict.get("raw_result_extension")):
                    await self.write_raw_result(task_id=task_id,
                                                data=raw_result,
                                                extension=extension)
                await self.write_result(task_id=task_id,
                                        data=task_data)
                await self.__tasks_service.set_status(id=task_id,
                                                      status=TaskStatus.finished)
                payload = WebSocketMessage(
                    title="Task status",
                    text=f"Task with {task_id=} {TaskStatus.finished}",
                    type="info"
                )
                await WS_MANAGER.send_message(project_id=project_id,
                                              message=payload)

    async def write_result(self, task_id: str, data: dict):
        task: Task = await self.__tasks_service.get_by_id(id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        restructor = get_restructor_for_task(task.created_by)
        entities = await restructor.restruct(**data)
        await self.__data_structure_service.make_magic(project_id=project_id,
                                                       scan_id=scan_id,
                                                       result=entities)
        await self.__tasks_service.set_status(id=task_id,
                                              status=TaskStatus.finished)

    # метод сервера на запись сырых данных результата на сервере
    async def write_raw_result(self,
                               task_id: str,
                               data: str,
                               extension: str):
        task: Task = await self.__tasks_service.get_by_id(id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        created_by = task.created_by
        project_path = ProjectFolders.get_path_for_project(project_id)
        scan_project_path = os.path.join(project_path, scan_id)
        if not os.path.exists(scan_project_path):
            os.makedirs(scan_project_path, exist_ok=True)
        restructor = get_restructor_for_task(task.created_by)
        data = restructor.get_raw_result(data)
        module_folder = get_folder_for_task(created_by)
        filename = f"{str(datetime.datetime.now())}_{created_by}_{task_id}"
        module_folder_path = os.path.join(project_path,
                                          scan_project_path,
                                          module_folder)
        if not os.path.exists(module_folder_path):
            os.makedirs(module_folder_path, exist_ok=True)
        file_path = os.path.join(module_folder_path,
                                 filename) + f".{extension}"
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(data)