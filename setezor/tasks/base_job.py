import asyncio
import traceback
from abc import abstractmethod
from aiojobs._job import Job
from setezor.schemas.task import TaskStatus
from setezor.logger import logger


class BaseJob(Job):
    def __init__(self, scheduler, name: str, update_graph: bool = True, agent_id: int | None = None):
        super().__init__(None, scheduler)  # FixMe add custom exception handler
        self.agent_id = agent_id
        self.name = name
        self.update_graph = update_graph

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

    async def soft_stop(self):
        pass

    async def hard_stop(self):
        pass

    async def get_status(self):
        return {
            self.active(): 'active',
            self.pending(): 'pending',
            self.closed(): 'finished'
        }[True]

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

    @staticmethod
    def local_task_notifier(func):
        async def wrapped(self, *args, **kwargs):
            task_id = self.task_id
            scan_id = self.scan_id
            project_id = self.project_id
            task_status_data = {
                "signal": "task_status",
                "task_id": task_id,
                "status": TaskStatus.started,
                "type": "success",
                "traceback": ""
            }
            await self.task_manager.task_status_changer_for_local_job(data=task_status_data, project_id=project_id)
            logger.debug(
                f"STARTED TASK {func.__qualname__}. {task_status_data}")
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                task_status_data["status"] = TaskStatus.failed
                task_status_data["traceback"] = str(e)
                task_status_data["type"] = "error"
                await self.task_manager.task_status_changer_for_local_job(data=task_status_data, project_id=project_id)
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
