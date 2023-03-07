from aiojobs._job import Job
from aiojobs._scheduler import Scheduler
import asyncio
from abc import abstractmethod
from routes.custom_types import MessageObserver
from exceptions.loggers import get_logger, LoggerNames


class BaseJob(Job):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, update_graph: bool = True):
        super().__init__(None, scheduler)  # FixMe add custom exception handler
        self.observer = observer
        self.name = name
        self.logger = get_logger(logger_name=LoggerNames.task)
        self.update_graph = update_graph
    
    @abstractmethod
    async def run(self, *args, **kwargs):
        pass
    
    async def soft_stop(self,):
        pass
    
    async def hard_stop(self,):
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
    
    
    def _start(self):
        self.observer.notify({'title': f'Task "{self.name}"', 
                              'text': f'Task "{self.name}" is started', 'type': 'info'}, 'message')
        return super()._start()
    
    async def _close(self, timeout):
        self.observer.notify({'title': f'Task "{self.name}"',
                              'text': f'Task "{self.name}" is closed', 'type': 'info'}, 'message')
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
                self.observer.notify({'title': f'Task "{self.name}"', 
                                    'text': f'Task "{self.name}" is failed.<br>Message {str(exc)}', 'type': 'error'}, 'message')
                scheduler._failed_tasks.put_nowait(task)
            else:
                if self.update_graph:
                    self.observer.notify({'command': 'update'}, 'message')
                self.observer.notify({'title': f'Task "{self.name}"', 
                              'text': f'Task "{self.name}" is finished.{"<br>Please update graph" if not self.update_graph else ""}', 'type': 'info'}, 'message')
        self._scheduler = None
        self._closed = True
        

class CustomScheduler(Scheduler):
    
    async def spawn_job(self, job: BaseJob) -> Job:
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        should_start = self._limit is None or self.active_count < self._limit
        if should_start:
            job._start()
        else:
            try:
                job.observer.notify({'title': f'Task "{job.name}"', 
                              'text': f'Task "{job.name}" is pending', 'type': 'info'}, 'message')
                await self._pending.put(job)
            except asyncio.CancelledError:
                await job.close()
                raise
        self._jobs.add(job)
        return job