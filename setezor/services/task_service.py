import json

from typing import List
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Task

class TasksService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, scan_id: str, params: dict, created_by:str, agent_id: int | None = None) -> Task:
        task_to_add = Task(
            status=TaskStatus.created, 
            project_id=project_id, 
            scan_id=scan_id,
            params=json.dumps(params),
            agent_id=agent_id,
            created_by=created_by
        )
        task_dict = task_to_add.model_dump()
        async with uow:
            task = await uow.task.add(task_dict)
            await uow.commit()
        message = WebSocketMessage(title="Task status", text=f"Task {task.id} {TaskStatus.created}",type="info")
        await WS_MANAGER.send_message(project_id=project_id, message=message) 
        return task

    @classmethod
    async def list(cls, uow: UnitOfWork, status: str, project_id: str) -> List[Task]:
        async with uow:
            tasks = await uow.task.filter(project_id=project_id, status=status)
        return tasks

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int, project_id: str) -> Task:
        async with uow:
            return await uow.task.find_one(id=id, project_id=project_id)

    @classmethod
    async def set_status(cls, uow: UnitOfWork, id: int, status: TaskStatus, project_id: str) -> int:
        async with uow:
            task_id = await uow.task.edit_one(id=id, data={"status": status})
            await uow.commit()
        message = WebSocketMessage(title="Task status", text=f"Task {id} {status}",type="info")
        await WS_MANAGER.send_message(project_id=project_id, message=message)    
        return task_id
