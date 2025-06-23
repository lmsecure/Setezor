import json

from typing import List
from setezor.tools.websocket_manager import WS_MANAGER
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Task


class TasksService(BaseService):
    async def create(self, project_id: str, scan_id: str, params: dict, created_by: str, agent_id: int | None = None) -> Task:
        task_to_add = Task(
            status=TaskStatus.created,
            project_id=project_id,
            scan_id=scan_id,
            params=json.dumps(params),
            agent_id=agent_id,
            created_by=created_by
        )
        task_dict = task_to_add.model_dump()
        async with self._uow:
            task = self._uow.task.add(task_dict)
            await self._uow.commit()
        return task

    async def list(self, status: str, project_id: str) -> List[Task]:
        async with self._uow:
            tasks = await self._uow.task.filter(project_id=project_id, status=status)
        return tasks

    async def get(self, id: int, project_id: str) -> Task:
        async with self._uow:
            return await self._uow.task.find_one(id=id, project_id=project_id)

    async def get_by_id(self, id: str) -> Task:
        async with self._uow:
            return await self._uow.task.find_one(id=id)

    async def set_status(self, id: int, status: TaskStatus, traceback: str = "") -> int:
        async with self._uow:
            task_id = await self._uow.task.edit_one(id=id, data={"status": status, "traceback": traceback})
            await self._uow.commit()
        return task_id
