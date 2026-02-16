import asyncio
import base64
import os
import traceback
from abc import abstractmethod
from aiojobs._job import Job
from fastapi import HTTPException

from setezor.models import Task
from setezor.schemas.task import TaskLog, TaskStatus
from setezor.logger import logger
from setezor.settings import PATH_PREFIX


class BaseJob(Job):
    logs_folder = None
    restructor = None

    def __init__(self, scheduler, name: str, update_graph: bool = True, agent_id: int | None = None):
        super().__init__(None, scheduler)  # FixMe add custom exception handler
        self.agent_id = agent_id
        self.name = name
        self.update_graph = update_graph

    @classmethod
    def get_task_by_class_name(cls, name: str):
        for model_class in BaseJob.__subclasses__():
            if model_class.__name__ == name:
                return model_class
        return None

    @classmethod
    @abstractmethod
    def generate_params_from_scope(cls, targets: list, **base_kwargs):
        pass

    @classmethod
    @logger.not_implemented
    def clean_payload(cls, version: str, payload: dict):
        pass

    @classmethod
    async def prepare_module(cls, module_path: str, agent_info: dict, *args, **kwargs):
        pass

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

    @logger.not_implemented
    async def soft_stop(self):
        pass

    @logger.not_implemented
    async def hard_stop(self):
        pass

    async def get_status(self):
        return {
            self.active(): 'active',
            self.pending(): 'pending',
            self.closed(): 'finished'
        }[True]

    @logger.not_implemented
    async def get_progress(self):
        pass

    async def close(self, *, timeout=None):
        return await super().close(timeout=timeout)

    @staticmethod
    def remote_task_notifier(func):
        async def wrapped(self, *args, **kwargs):
            task_id = self.task_id
            agent_id = self.agent_id
            task_status_data = {
                "signal": "task_status",
                "task_id": task_id,
                "status": TaskStatus.started,
                "type": "success",
                "traceback": ""
            }
            await self.task_manager.notify(agent_id=agent_id,   # меняем инфу по статусу задачи на сервере
                                 data=task_status_data)
            logger.debug(f"STARTED TASK {func.__qualname__}")
            try:
                result, raw_result_extension = await func(self, *args, **kwargs)
            except Exception as e:
                task_status_data["status"] = TaskStatus.failed
                task_status_data["traceback"] = str(e)
                task_status_data["type"] = "error"

                await self.task_manager.notify(agent_id=agent_id,   # меняем инфу по статусу задачи на сервере
                                     data=task_status_data)
                logger.error(
                    f"TASK {func.__qualname__} FAILED. {traceback.format_exc()}")
                return
            await self.task_manager.send_result_to_parent_agent(
                task_id=task_id,
                agent_id=agent_id,
                result=result,
                raw_result_extension=raw_result_extension
            )
            return result
        return wrapped

    @classmethod
    def get_task_logs(cls, task: Task, **kwargs) -> list[TaskLog]:
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        if not task_class.logs_folder:
            raise HTTPException(status_code=404, detail="Log file not found")
        file_path = os.path.join(PATH_PREFIX, "projects", task.project_id, task.scan_id, task_class.logs_folder)
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

        return [TaskLog(type=cls.logs_folder, file_name=file_name, file_data=base64.b64encode(file_data))]

    @staticmethod
    def local_task_notifier(func):
        async def wrapped(self, *args, **kwargs):
            task_id = self.task_id
            scan_id = self.scan_id
            project_id = self.project_id
            agent_id = self.agent_id
            task_status_data = {
                "signal": "task_status",
                "task_id": task_id,
                "status": TaskStatus.started,
                "type": "success",
                "traceback": ""
            }
            await self.task_manager.task_status_changer_for_local_job(data=task_status_data, agent_id=agent_id)
            logger.debug(
                f"STARTED TASK {func.__qualname__}. {task_status_data}")
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                task_status_data["status"] = TaskStatus.failed
                task_status_data["traceback"] = str(e)
                task_status_data["type"] = "error"
                await self.task_manager.task_status_changer_for_local_job(data=task_status_data, agent_id=agent_id)
                logger.error(
                    f"TASK {func.__qualname__} FAILED. {traceback.format_exc()}")
                return
            await self.task_manager.local_writer(project_id=project_id,
                                       task_id=task_id,
                                       scan_id=scan_id,
                                       result=result)
            return result
        return wrapped

    async def _close(self, timeout):
        return await super()._close(timeout)

    def _done_callback(self, task):
        scheduler = self._scheduler
        scheduler._done(self)
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            pass
        else:
            if exc is not None and not self._explicit:
                self._report_exception(exc)
                scheduler._failed_tasks.put_nowait(task)
            else:
                ...
        self._scheduler = None
        self._closed = True
