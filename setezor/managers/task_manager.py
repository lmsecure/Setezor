from typing import Callable
from fastapi import HTTPException
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
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.managers.agent_manager import AgentManager
from setezor.managers.sender_manager import HTTPManager
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
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if status == 200:
                break
        return


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
            next_agent_url = payload.pop("next_agent_url")
            data, status = await HTTPManager.send_json(url=next_agent_url, data=payload)
            if status == 200:
                break
        return True


    @classmethod
    async def delete_task(cls, uow: UnitOfWork, id: str, project_id: str) -> bool:
        task: Task = await TasksService.get(uow=uow, id=id, project_id=project_id)
        if not task:
            return False
        await TasksService.set_status(uow=uow, id=id, status=TaskStatus.failed, traceback="User canceled the task")
        return True

    @classmethod  # метод агента на создание шедулера
    def create_new_scheduler(cls, job: BaseJob):
        if job in cls.schedulers:
            return cls.schedulers[job]
        new_scheduler = SchedulerManager.for_job(job=job)
        cls.schedulers[job] = new_scheduler
        new_scheduler.attach(cls)
        return new_scheduler


    @classmethod
    async def task_status_changer_for_local_job(cls, data: dict, uow: UnitOfWork, project_id: str):
        await AgentManager.proceed_signal(dict_data=data, uow=uow, project_id=project_id)
        if data.get("signal") == "task_status" and data.get("status") == TaskStatus.failed:
            cls.delete_task(task_id=data.get("task_id"))

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
        cls.delete_task(task_id=task_id)

    @classmethod
    def delete_task(cls, task_id: str):
        cls.tasks.pop(task_id, None)