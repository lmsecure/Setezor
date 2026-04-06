import json
import os
from datetime import datetime
from typing import List

from fastapi import HTTPException

from setezor.schemas.roles import Roles
from setezor.schemas.task import TaskLog, TaskStatus
from setezor.services.base_service import BaseService
from setezor.models import Task, UserProject
from setezor.tasks.base_job import BaseJob
from setezor.settings import PATH_PREFIX


class TasksService(BaseService):
    async def create(self, project_id: str, scan_id: str, user_id: str, params: dict, created_by: str, agent_id: str | None = None) -> Task:
        task_to_add = Task(
            status=TaskStatus.created,
            project_id=project_id,
            scan_id=scan_id,
            user_id=user_id,
            params=json.dumps(params),
            agent_id=agent_id,
            created_by=created_by
        )
        task_dict = task_to_add.model_dump()
        async with self._uow:
            task = self._uow.task.add(task_dict)
            await self._uow.commit()
        return task

    async def list(self, status: list, project_id: str) -> list[dict]:
        async with self._uow:
            tasks = await self._uow.task.filter(project_id=project_id, status=status)
        result = []
        for task in tasks:
            task_class = BaseJob.get_task_by_class_name(task.created_by)
            if not task_class:
                continue
            file_path = os.path.join(PATH_PREFIX, "projects", project_id, task.scan_id, task_class.logs_folder) if task_class.logs_folder else None

            try:
                folders = task_class.folders
                is_log = True
            except AttributeError:
                is_log = any([file_name for file_name in os.listdir(file_path) if task.id in file_name]) if file_path and os.path.exists(file_path) else False

            result.append({
                "id": task.id,
                "created_by": task.created_by,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "params": task.params,
                "error": task.traceback,
                "is_log": is_log
            })
        return result

    async def get(self, id: int, project_id: str) -> Task:
        async with self._uow:
            return await self._uow.task.find_one(id=id, project_id=project_id)

    async def get_by_id(self, id: str) -> Task:
        async with self._uow:
            return await self._uow.task.find_one(id=id)

    async def set_status(self, id: str, status: TaskStatus, traceback: str = "") -> str:
        async with self._uow:
            task_id = await self._uow.task.edit_one(id=id, data={"status": status, "traceback": traceback})
            await self._uow.commit()
        return task_id

    async def list_tasks_for_user_agent_to_cancel(self, id: str) -> str:
        async with self._uow:
            tasks = await self._uow.task.get_agent_tasks_to_cancel(agent_id=id)
        return tasks

    async def count_of_running_tasks_on_agent(self, agent_id: str):
        async with self._uow:
            return await self._uow.task.count_of_running_tasks_on_agent(agent_id=agent_id)

    async def get_task_raw_logs(
        self,
        project_id: str,
        task_id: str,
        user_id: str
    ) -> List[TaskLog]:
        async with self._uow:
            task: Task = await self._uow.task.find_one(id=task_id, project_id=project_id, user_id=user_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            task.project_id = project_id
            task_class = BaseJob.get_task_by_class_name(task.created_by)
            return task_class.get_task_logs(task)

    async def get_tasks_tabulator_data(
            self,
            project_id: str,
            user_id: str,
            status: str,
            page: int,
            size: int,
            sort: str = "[]",
            filter: str = "[]"
    ) -> tuple[int, List]:
        try:
            sort_params = json.loads(sort) if sort != "[]" else []
            filter_params = json.loads(filter) if filter != "[]" else []
        except json.JSONDecodeError:
            sort_params = []
            filter_params = []
        async with self._uow:
            if status == "CANCELED":
                statuses = ["CANCELED", "PRE_CANCELED", "SOFTSTOPPED", "STOPPED"]
            elif status == "STARTED":
                statuses = ["PROCESSING_ON_AGENT", "FINISHED_ON_AGENT", "PROCESSING_ON_SERVER"]
            else:
                statuses = [status]

            user: UserProject = await self._uow.user_project.find_one(user_id=user_id, project_id=project_id)

            total, rows = await self._uow.task.get_tasks_data(
                project_id=project_id,
                user_role=user.role.name,
                statuses=statuses,
                page=page,
                size=size,
                sort_params=sort_params or [],
                filter_params=filter_params or [])

        res_rows = []
        for row in rows:
            items = []
            for item in row:
                if isinstance(item, datetime):
                    item = datetime.strftime(item, "%Y-%m-%d %H:%M:%S")

                items.append(item)
            res_rows.append(items)

        keys = ["id", "task_id", "created_by", "created_at", "updated_at", "params", "error", "scan_id"]
        if user.role.name == Roles.owner:
            keys.append("user_id")
        tabulator = [
            dict(zip(keys, [i] + list(row))) for i, row in enumerate(res_rows, 1)
        ]
        for row in tabulator:
            try:
                row["params"] = json.loads(row["params"])
                row["agent_id"] = row["params"].get("agent_id")
            except json.JSONDecodeError:
                pass

            task_class = BaseJob.get_task_by_class_name(row["created_by"])
            if not task_class:
                continue
            file_path = os.path.join(PATH_PREFIX, "projects", project_id, row["scan_id"], task_class.logs_folder) if task_class.logs_folder else None

            try:
                folders = task_class.folders
                is_log = True
            except AttributeError:
                is_log = any([file_name for file_name in os.listdir(file_path) if row["task_id"] in file_name]) if file_path and os.path.exists(file_path) else False

            row["is_log"] = is_log

        return total, tabulator