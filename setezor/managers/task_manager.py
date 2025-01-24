import io
import pickle
import aiohttp
from fastapi import HTTPException
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.services.data_structure_service import DataStructureService
from setezor.tasks.base_job import BaseJob, CustomScheduler
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Task
from setezor.services import TasksService
from setezor.schemas.task import TaskPayload, \
    TaskStatus, WebSocketMessage, \
    WebSocketMessageForProject
from setezor.tasks import get_task_by_class_name
from setezor.spy import Spy
from setezor.managers import agent_manager as AM


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        full_name = f"{module}.{name}"
        if (full_name.startswith("setezor") or
                full_name.startswith("sqlalchemy") or
                full_name.startswith("datetime")
            ):
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Недопустимый класс: {full_name}")

def restricted_loads(data):
    file_like = io.BytesIO(data)
    return RestrictedUnpickler(file_like).load()

class TaskManager:

    scheduler = None

    @classmethod  # метод сервера на создание локальной
    async def create_local_job(cls, job: BaseJob, uow: UnitOfWork, project_id: str, scan_id: str, **kwargs) -> Task:
        agent_id = kwargs.pop("agent_id", None)
        task: Task = await TasksService.create(uow=uow, project_id=project_id, scan_id=scan_id, params=kwargs, agent_id=agent_id, created_by=job.__name__)
        await cls.start_local_job(uow=uow, job=job, id=task.id, agent_id=agent_id, project_id=project_id, scan_id=scan_id, **kwargs)
        return task

    @classmethod  # метод сервера на запуск локальной джобы
    async def start_local_job(cls, job: BaseJob, uow: UnitOfWork, project_id: str, id: str, agent_id: str, **kwargs):
        if not cls.scheduler:
            cls.scheduler = await cls.create_new_scheduler()
        new_job: BaseJob = job(
            agent_id=agent_id,
            name=f"Task {id}",
            scheduler=cls.scheduler,
            uow=uow,
            task_id=id,
            project_id=project_id,
            **kwargs
        )
        job: BaseJob = await cls.scheduler.spawn_job(new_job)
        await TasksService.set_status(uow=uow, id=id, status=TaskStatus.started, project_id=project_id)
        await new_job._start()
        return id

    @classmethod # метод сервера на создание джобы на агенте
    async def create_job(cls, job: BaseJob, uow: UnitOfWork, project_id: str, scan_id: str, **kwargs) -> Task:
        agent_id = kwargs.get("agent_id")
        async with uow:
            agent = await uow.agent.find_one(id=agent_id, project_id=project_id)
        if not agent.parent_agent_id:
            message = WebSocketMessage(title="Error", text=f"Agent {agent.name} has no parent agent", type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message) 
            raise HTTPException(status_code=403, detail="No scan picked")
        if not agent.secret_key:
            message = WebSocketMessage(title="Error", text=f"Agent {agent.name} has no secret key", type="error")
            await WS_MANAGER.send_message(project_id=project_id, message=message) 
            raise HTTPException(status_code=403, detail="No scan picked")
        task: Task = await TasksService.create(uow=uow, project_id=project_id, 
                                               scan_id=scan_id,
                                               params=kwargs, agent_id=agent_id, created_by=job.__name__)
        agents_chain = await AM.AgentManager.get_agents_chain(uow=uow, agent_id=agent_id, project_id=project_id)
        task_in_agent_chain = TaskPayload(
            task_id=task.id,
            project_id=project_id,
            agent_id=agent_id,
            job_name=job.__name__,
            job_params=kwargs,
        )
        data = {
            "signal": "create_task",
            "agent_id": agent_id,
            "project_id": project_id,
            **task_in_agent_chain.model_dump()
        }
        payload = AM.AgentManager.cipherPayload(agents_chain=agents_chain, data=data, close_connection=True)
        body = payload["data"].encode()
        data = await AM.AgentManager.send_bytes(url=payload["next_agent_url"], data=body)
        return task
    
    @classmethod # метод сервера на запуск джобы на агенте
    async def start_job(cls, uow: UnitOfWork, id: str, project_id: str):
        task: Task = await TasksService.get(uow=uow, id=id, project_id=project_id)
        agents_chain = await AM.AgentManager.get_agents_chain(uow=uow, agent_id=task.agent_id, project_id=project_id)
        data = {
            "signal": "start_task",
            "id": task.id,
            "agent_id": task.agent_id,
            "project_id": task.project_id
        }
        payload = AM.AgentManager.cipherPayload(agents_chain=agents_chain, data=data, close_connection=True)
        body = payload["data"].encode()
        data = await AM.AgentManager.send_bytes(url=payload["next_agent_url"], data=body)

        await TasksService.set_status(uow=uow, id=id, status=TaskStatus.started, project_id=task.project_id)
        
        return True
    
    

    @classmethod # метод агента на создание джобы
    async def create_job_on_agent(cls, payload: TaskPayload) -> Task:
        if not cls.scheduler:
            cls.scheduler = await cls.create_new_scheduler()
        job_cls = get_task_by_class_name(payload.job_name)
        task_id = payload.task_id
        project_id = payload.project_id
        agent_id = payload.agent_id
        new_job: BaseJob = job_cls(
            name=f"Task {task_id}",
            scheduler=cls.scheduler,
            task_id=task_id,
            project_id=project_id,
            **payload.job_params
        )
        job: BaseJob = await cls.scheduler.spawn_job(new_job)
        ws_message = WebSocketMessageForProject(project_id=project_id, title="Info from agent", text=f"I registered task with {task_id = }", type="info")
        data_for_server = AM.AgentManager.generate_websocket_message(agent_id=agent_id, message=ws_message)
        await cls.send_request(url=f"{Spy.PARENT_AGENT_URL}/api/v1/agents/backward", data=data_for_server)
        return task_id

    @classmethod # метод агента на запуск джобы
    async def start_job_on_agent(cls, id: str) -> str:
        for task in cls.scheduler.jobs:
            if task.task_id == id:
                await task._start()
                message = WebSocketMessageForProject(project_id=task.project_id, title="Info from agent", text=f"I started task with task_id = {task.task_id}", type="info")
                data_for_server = AM.AgentManager.generate_websocket_message(agent_id=task.agent_id, message=message)
                await cls.send_request(url=f"{Spy.PARENT_AGENT_URL}/api/v1/agents/backward", data=data_for_server)
                break
        return id

    
    @classmethod
    async def soft_stop_task(cls, uow: UnitOfWork, id: str, project_id: str) -> bool:
        task: Task = await TasksService.get(uow=uow, id=id, project_id=project_id)
        agents_chain = await AM.AgentManager.get_agents_chain(uow=uow, agent_id=task.agent_id, project_id=project_id)
        data = {
            "signal": "soft_stop_task",
            "id": id,
        }
        payload = AM.AgentManager.cipherPayload(agents_chain=agents_chain, data=data, close_connection=True)
        body = payload["data"].encode()
        data = await AM.AgentManager.send_bytes(url=payload["next_agent_url"], data=body)
        return True

    @classmethod # метод агента на мягкое завершение таски
    async def soft_stop_task_on_agent(cls, id: str) -> str:
        for task in cls.scheduler.jobs:
            if task.task_id == id:
                await task.soft_stop()
                message = WebSocketMessageForProject(project_id=task.project_id, title="Info from agent", text=f"I stopped task with task_id = {task.task_id}", type="info")
                data_for_server = AM.AgentManager.generate_websocket_message(agent_id=task.agent_id, message=message)
                await cls.send_request(url=f"{Spy.PARENT_AGENT_URL}/api/v1/agents/backward", data=data_for_server)
                break
        return id

    @classmethod # метод агента на создание шедулера
    async def create_new_scheduler(cls):
        return CustomScheduler()


    @classmethod # метод сервера на запись результата на сервере
    async def write_result(cls, task_id: str, data: bytes, uow: UnitOfWork):
        result = restricted_loads(data)
        async with uow:
            task = await uow.task.find_one(id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        service = DataStructureService(uow=uow, project_id=project_id, scan_id=scan_id, result=result)
        await service.make_magic()
        await TasksService.set_status(uow=uow, id=task_id, status=TaskStatus.finished, project_id=project_id)


    @staticmethod # метод агента на отправку результата на предыдущего агента
    async def send_bytes(url: str, data: dict | list[dict]):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, ssl=False) as resp:
                return resp.status
            
    
    @classmethod # метод сервера и агента на отправку следующему звену
    async def send_request(cls, url: str, data: dict | list[dict]):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, ssl=False) as resp:
                    return resp.status
        except:
            if project_id := data.get("project_id"):
                message = WebSocketMessageForProject(project_id=project_id, title="Info", text=f"{url} is unreachable", type="error")
                await cls.notify_server(message=message)

