import json

import os
import base64

from typing import List
from setezor.schemas.task import TaskStatus
from setezor.services.base_service import BaseService
from setezor.models import Task
from setezor.tasks.base_job import BaseJob

from fastapi import HTTPException

from setezor.settings import PATH_PREFIX


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

    async def get_task_raw_log(self, project_id: str, task_id: str) -> tuple[str, bytes]:
        async with self._uow:
            task = await self._uow.task.find_one(id=task_id, project_id=project_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        if not task_class.logs_folder:
            raise HTTPException(status_code=404, detail="Log file not found")
        file_path = os.path.join(PATH_PREFIX, "projects", project_id, task.scan_id, task_class.logs_folder)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Log file not found")
        files = os.listdir(file_path)
        file_data = b''
        file_name = ""
        for file_n in files:
            if task.id in file_n:
                with open(os.path.join(file_path, file_n), 'rb') as f:
                    file_name = f"{task.id}.{file_n.rpartition('.')[-1]}"
                    file_data = f.read()
                break
        else:
            raise HTTPException(status_code=404, detail="Log file not found")
        if not file_data:
            raise HTTPException(status_code=400, detail="Log file is empty")
        return file_name, base64.b64encode(file_data)
