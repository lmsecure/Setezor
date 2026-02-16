import base64
import copy
import datetime
import json
import orjson
from typing import Annotated, Callable
from fastapi import Depends, HTTPException
from setezor.models.agent import Agent
from setezor.schemas.agent import BackWardData
from setezor.tools.cipher_manager import Cryptor
from setezor.tools.file_manager import FileManager
from setezor.tools.scheduler_manager import SchedulerManager
from setezor.tools.websocket_manager import WS_MANAGER, WS_USER_MANAGER
from setezor.services.agent_in_project_service import AgentInProjectService
from setezor.services.agent_service import AgentService
from setezor.data_writer.data_structure_service import DataStructureService
from setezor.services.scope_service import ScopeService
from setezor.tasks.base_job import BaseJob
from setezor.tasks.speed_test_task import SpeedTestServerTask, SpeedTestClientTask
from setezor.models import Task
from setezor.services import TasksService
from setezor.schemas.task import TaskPayload, \
    TaskStatus, WebSocketMessage
from setezor.managers.agent_manager import AgentManager
from setezor.tools.sender_manager import HTTPManager
from setezor.logger import logger
from setezor.settings import PROJECTS_DIR_PATH


class TaskParams:
    def __init__(self, kwargs: dict, job: BaseJob, tm: "TaskManager", project_id: str):
        self.kwargs = copy.deepcopy(kwargs)
        self.params = []
        self.job = job
        self.task_manager = tm
        self.project_id = project_id

        self.scope_id = self.kwargs.pop("scope_id", None)
        self.agents_interfaces = self.kwargs.pop("agents_interfaces", None)

    def __iter__(self):
        return iter(self.params)

    async def scope_proceeder(self):
        if not self.scope_id:
            self.params = [self.kwargs]
            return
        scope_targets = await self.task_manager.scope_service.get_targets(project_id=self.project_id,
                                                                          id=self.scope_id)
        self.params = self.job.generate_params_from_scope(targets=scope_targets, **self.kwargs)


class TaskParamsPreparer:
    @classmethod
    def prepare(cls, func: Callable) -> Callable:
        async def inner(self, job: BaseJob, project_id: str,
                        scan_id: str, **kwargs):
            params = TaskParams(kwargs=kwargs,
                                job=job,
                                tm=self,
                                project_id=project_id)
            await params.scope_proceeder()

            for param in params:
                await func(self, job=job,
                           project_id=project_id,
                           scan_id=scan_id,
                           **param)
        return inner


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
        file_manager: FileManager
    ):
        self.__tasks_service: TasksService = tasks_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service
        self.__agent_service: AgentService = agent_service
        self.__data_structure_service: DataStructureService = data_structure_service
        self.__scope_service: ScopeService = scope_service
        self.__agent_manager: AgentManager = agent_manager
        self.__file_manager: FileManager = file_manager

    @property
    def scope_service(self):
        return self.__scope_service

    @property
    def tasks_service(self):
        return self.__tasks_service

    @property
    def file_manager(self):
        return self.__file_manager

    async def notify_by_websocket(self, message: WebSocketMessage, task: Task = None, project_id: str = None):
        if not task and not project_id:
            raise Exception('Task or project_id is required')
        if task and task.project_id or project_id:
            await WS_MANAGER.send_message(entity_id=project_id or task.project_id, message=message)
        else:
            await WS_USER_MANAGER.send_message(entity_id=task.user_id, message=message)

    # метод сервера на создание локальной задачи
    async def create_local_job(self,
                               job: BaseJob,
                               project_id: str,
                               user_id: str,
                               scan_id: str,
                               **kwargs) -> Task:
        def safe_json(obj):
            try:
                json.dumps(obj)
                return True
            except TypeError:
                return False

        safe_params = {k: v for k, v in kwargs.items() if safe_json(v)}
        header_data = safe_params.pop("file", None) or safe_params.pop("log_file", None)
        unknown_agent_id = kwargs.get("agent_id")
        agent_in_project = await self.__agent_in_project_service.get_agent_in_project(id=unknown_agent_id)
        if agent_in_project:
            agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        else:
            agent = await self.__agent_service.get_by_id(id=unknown_agent_id)
        task: Task = await self.__tasks_service.create(user_id=user_id,
                                                       project_id=project_id,
                                                       scan_id=scan_id,
                                                       params=safe_params,
                                                       agent_id=agent.id if agent else None,
                                                       created_by=job.__name__)
        if header_data:
            task_class = BaseJob.get_task_by_class_name(task.created_by)
            filename = f"{str(datetime.datetime.now())}_{task.created_by}_{task.id}"
            data = base64.b64decode(header_data.split(',')[1])
            input_filename = safe_params.get("filename", '')
            extension =  ''.join(input_filename.rpartition('.')[1:]) if '.' in input_filename else ''
            await self.__file_manager.save_file(
                file_path=[PROJECTS_DIR_PATH, task.project_id, task.scan_id, task_class.logs_folder, f"{filename}{extension}"],
                data=data
            )

        message = WebSocketMessage(
            title="Task status", text=f"Task {task.id = } {TaskStatus.created}", type="info")
        await self.notify_by_websocket(message, task)
        logger.debug(f"CREATED TASK {job.__qualname__} {task.id} {safe_params}")
        scheduler = self.create_new_scheduler(job)
        new_job: BaseJob = job(
            task_manager=self,
            name=f"Task {task.id}",
            scheduler=scheduler,
            task_id=task.id,
            project_id=project_id,
            scan_id=scan_id,
            **kwargs
        )
        job: BaseJob = await scheduler.spawn_job(new_job)

        return task

    def task_is_os_the_agent(self, job: BaseJob, agent: Agent) -> bool:
        if not agent.information:
            return False
        allowed_tasks = json.loads(agent.information).get("tasks", {})
        if job.__name__ not in allowed_tasks:
            return False
        # поле module_is_installed появилось с версии > 1.0.5
        if "module_is_installed" in allowed_tasks.get(job.__name__, {}):
            if not allowed_tasks.get(job.__name__, {}).get("module_is_installed"):
                return False
        return True

    def clean_payload(self, job: BaseJob, agent: Agent, payload: dict):
        if not agent.information:
            return
        version = json.loads(agent.information).get("version")
        if not version:
            return
        job.clean_payload(version=version, payload=payload)

    # метод сервера на создание джобы на агенте
    @TaskParamsPreparer.prepare
    async def create_job(self, job: BaseJob,
                         user_id: str,
                         project_id: str,
                         scan_id: str,
                         signal: str = "create_task",
                         **kwargs) -> Task:
        unknown_agent_id = kwargs.get("agent_id")
        agent_in_project = await self.__agent_in_project_service.get_agent_in_project(id=unknown_agent_id)
        if agent_in_project:
            agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        else:
            agent = await self.__agent_service.get_by_id(id=unknown_agent_id)
        if not agent.rest_url:
            message = WebSocketMessage(title="Error",
                                       text=f"Agent {agent.name} is synthetic",
                                       type="error")
            await self.notify_by_websocket(message, project_id=project_id)
            raise HTTPException(status_code=403,
                                detail=f"Agent {agent.name} is synthetic")
        if not agent.secret_key:
            message = WebSocketMessage(title="Error",
                                       text=f"Agent {
                                           agent.name} has no secret key",
                                       type="error")
            await self.notify_by_websocket(message, project_id=project_id)
            raise HTTPException(status_code=403,
                                detail=f"Agent {agent.name} has no secret key")
        if not self.task_is_os_the_agent(job=job, agent=agent):
            message = WebSocketMessage(title="Error",
                        text=f"The selected agent {agent.name} is not able to perform this task {job.__name__}.",
                        type="error")
            module_name = json.loads(agent.information).get("tasks", {}).get(job.__name__).get("module_name")
            if module_name:
                message = WebSocketMessage(title="no title",
                            command="install_module",
                            text=json.dumps({"agent_id": agent.id, "module_name": module_name, "project_id": project_id}),
                            type="no type")
            await self.notify_by_websocket(message, project_id=project_id)
            raise HTTPException(
                status_code=406,
                detail="The selected agent is not able to perform this task" + f" Module name: {module_name}" if module_name else "",
            )
        self.clean_payload(job=job, agent=agent, payload=kwargs)

        agents_chain = await self.__agent_service.get_agents_chain(agent_id=agent.id,
                                                                   user_id=agent.user_id)
        task: Task = await self.__tasks_service.create(project_id=project_id,
                                                       scan_id=scan_id,
                                                       user_id=user_id,
                                                       params=kwargs,
                                                       agent_id=agent.id,
                                                       created_by=job.__name__)

        message = WebSocketMessage(title="Task status",
                                   text=f"Task {task.id} {TaskStatus.created}",
                                   type="info")
        await self.notify_by_websocket(message, task)

        task_in_agent_chain = TaskPayload(
            task_id=task.id,
            project_id=project_id,
            agent_id=unknown_agent_id,
            job_name=job.__name__,
            job_params=kwargs,
        )
        data = {
            "signal": signal,
            "agent_id": unknown_agent_id,
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
                logger.info(f'Task created | {job.__qualname__} {kwargs}')
                break
        return

    async def soft_stop_task(self, id: str, project_id: str) -> bool:
        task: Task = await self.__tasks_service.get(id=id, project_id=project_id)
        await self.__tasks_service.set_status(id=id, status=TaskStatus.soft_stopped)
        agent_in_project = await self.__agent_in_project_service.get_agent_by_project_id(
            project_id=project_id, agent_id=task.agent_id
        )
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
                logger.info(f'Task stopped | task_id: {id}, project_id: {project_id}')
                break
        return True
    
    async def cancel_task(self, id: str, project_id: str) -> bool:
        task: Task = await self.__tasks_service.get(id=id, project_id=project_id)
        await self.__tasks_service.set_status(id=id, status=TaskStatus.pre_canceled)
        agent_in_project = await self.__agent_in_project_service.get_agent_by_project_id(
            project_id=project_id, agent_id=task.agent_id
        )
        agent = await self.__agent_service.get_by_id(id=agent_in_project.agent_id)
        agents_chain = await self.__agent_service.get_agents_chain(agent_id=agent_in_project.agent_id,
                                                                   user_id=agent.user_id)
        data = {
            "signal": "cancel_task",
            "id": id,
        }
        for chain in agents_chain:
            payload = self.__agent_manager.cipher_chain(
                agents_chain=chain, data=data, close_connection=True)
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if status == 200:
                logger.info(f'Task canceled | task_id: {id}, project_id: {project_id}')
                break
        return True

    # метод агента на создание шедулера
    def create_new_scheduler(self, job: BaseJob):
        if job in self.schedulers:
            return self.schedulers[job]
        new_scheduler = SchedulerManager.for_job(job=job)
        self.schedulers[job] = new_scheduler
        return new_scheduler

    async def task_status_changer_for_local_job(self, data: dict, agent_id: str):
        await self.proceed_signal(dict_data=data, agent_id=agent_id)
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
        message = WebSocketMessage(
            title="Task status",
            text=f"Task with {task_id = } {TaskStatus.finished}",
            type="info"
        )
        logger.info(f'FINISHED {task_id = }')
        await self.notify_by_websocket(message, project_id=project_id)
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
        file_manager: Annotated[FileManager, Depends(FileManager.new_instance)]
    ):
        return cls(
            tasks_service=tasks_service,
            agent_in_project_service=agent_in_project_service,
            agent_service=agent_service,
            data_structure_service=data_structure_service,
            scope_service=scope_service,
            agent_manager=agent_manager,
            file_manager=file_manager
        )

    async def autostart_speed_test_client(self, task_id: str):
        task = await self.__tasks_service.get_by_id(id=task_id)
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        if not (task_class is SpeedTestServerTask):
            return
        task_params = json.loads(task.params)
        task_params["agent_id"] = task_params.get("agent_id_from")
        await self.create_job(job=SpeedTestClientTask,
                              user_id=task.user_id,
                              project_id=task.project_id,
                              scan_id=task.scan_id,
                              **task_params)

    async def decipher_data_from_project_agent(self, data: BackWardData):
        unknown_agent = await self.__agent_in_project_service.get_agent_in_project(id=data.sender)
        if unknown_agent:
            agent = await self.__agent_service.get_by_id(id=unknown_agent.agent_id)
        else:
            agent = await self.__agent_service.get_by_id(id=data.sender)
        if agent:
            await self.__agent_service.set_last_time_seen(id=agent.id)
            try:
                dict_data = self._decipher_payload(
                    data.data, key=agent.secret_key)
            except ValueError:
                return
            await self.proceed_signal(dict_data=dict_data, agent_id=agent.id)

    def _decipher_payload(self, payload: str, key: str) -> dict:
        ciphered_payload = payload.encode()
        b64decoded = base64.b64decode(ciphered_payload)
        deciphered_payload = Cryptor.decrypt(data=b64decoded, key=key)
        return orjson.loads(deciphered_payload)

    async def proceed_signal(self, dict_data: dict, agent_id: str):
        copy_of_dict = copy.deepcopy(dict_data)
        signal = copy_of_dict.pop("signal", None)
        if (task_id := copy_of_dict.get("task_id")):
            task: Task = await self.__tasks_service.get_by_id(id=task_id)
        match signal:
            case "notify":
                message = WebSocketMessage(**copy_of_dict)
                await self.notify_by_websocket(message, task)
            case "job_status":
                message = WebSocketMessage(
                    title="Job status",
                    text=f"Task with task_id = {task_id} {
                        copy_of_dict["status"]} {copy_of_dict["traceback"]}",
                    type=copy_of_dict["type"]
                )
                await self.__tasks_service.set_status(id=task_id,
                                                      status=copy_of_dict["status"],
                                                      traceback=copy_of_dict["traceback"])
                await self.notify_by_websocket(message, task)
            case "task_status":
                await self.__tasks_service.set_status(id=task_id,
                                                      status=copy_of_dict["status"],
                                                      traceback=copy_of_dict["traceback"])
                message = WebSocketMessage(
                    title="Task status",
                    text=f"Task with task_id = {task_id} {
                        copy_of_dict["status"]} {copy_of_dict["traceback"]}",
                    type=copy_of_dict["type"]
                )
                await self.notify_by_websocket(message, task)
                ##################################
                if copy_of_dict["status"] == TaskStatus.started:
                    await self.autostart_speed_test_client(task_id=task_id)
                ##################################

            case "result_entities":
                task_data = copy_of_dict["result"]
                if (raw_result := task_data.get("raw_result")) and (extension := copy_of_dict.get("raw_result_extension")):
                    await self.write_raw_result(task_id=task_id,
                                                data=raw_result,
                                                extension=extension)
                await self.write_result(task_id=task_id,
                                        data=task_data)
                await self.__tasks_service.set_status(id=task_id,
                                                      status=TaskStatus.finished)
                logger.info(f'FINISHED TASK {task_id}')
                message = WebSocketMessage(
                    title="Task status",
                    text=f"Task with {task_id = } {TaskStatus.finished}",
                    type="info"
                )
                await self.notify_by_websocket(message, task)
                if task.created_by == 'PushModuleTask':
                    module_name = json.loads(task.params)['module_name']
                    message = WebSocketMessage(
                        title="Install module",
                        text=f"Module {module_name} successfully installed",
                        type="info"
                    )
                    await WS_USER_MANAGER.send_message(entity_id=task.user_id, message=message)

            case "information":
                await self.__agent_service.set_info(id=agent_id, info=json.dumps(copy_of_dict))
            case _:
                logger.error(f'Unknown signal: {signal}', exc_info=False)

    async def write_result(self, task_id: str, data: dict):
        task: Task = await self.__tasks_service.get_by_id(id=task_id)
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        project_id = task.project_id
        scan_id = task.scan_id
        # data["agent_id"] = task.agent_id      # TODO: может упасть
        data["project_id"] = project_id
        data["scan_id"] = scan_id
        data["task_id"] = task_id
        if not task_class.restructor:
            logger.debug(f"Task {task.created_by} {task_id} does not have restructor")
            return
        entities = await task_class.restructor.restruct(**data)
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
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        if not task_class.restructor:
            logger.debug(f"Task {task.created_by} {task_id} does not have restructor")
            return
        data = task_class.restructor.get_raw_result(data)
        filename = f"{str(datetime.datetime.now())}_{task.created_by}_{task_id}"
        await self.__file_manager.save_file(file_path=[PROJECTS_DIR_PATH, task.project_id, task.scan_id,
                                                               task_class.logs_folder, f"{filename}.{extension}"], data=data)
