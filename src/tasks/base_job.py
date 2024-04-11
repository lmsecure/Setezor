import asyncio
from typing import Coroutine, Any
from datetime import datetime
from abc import abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from subprocess import Popen, PIPE
from dataclasses import dataclass, field
from aiojobs._job import Job
from aiojobs._scheduler import Scheduler

try:
    from app_routes.custom_types import MessageObserver
    from exceptions.loggers import get_logger, LoggerNames
except ImportError:
    from ..app_routes.custom_types import MessageObserver
    from ..exceptions.loggers import get_logger, LoggerNames

@dataclass(slots=True, unsafe_hash=True, frozen=True)
class SubprocessResult:
    
    command: list[str]
    return_code: int
    result: str
    error: str
    start_time: datetime
    end_time: datetime = field(default_factory=datetime.now)
    

class SubprocessJob(Coroutine):
    
    
    def __init__(self, command: list[str], loop: asyncio.BaseEventLoop = None, 
                 executor: ThreadPoolExecutor | ProcessPoolExecutor = ThreadPoolExecutor()) -> None:
        self.command = command
        self.executor = executor
        self.loop = loop
        
    def _run_subprocess(self):
        
        """Запускает суброцесс, возвращает результат, ошибку, код возврата.
        Текст результата и ошибки, кодируется в utf8, ошибки кодировке обрабатываются 
        c параметром `backslashreplace`
        """
        
        with Popen(self.command, stdin=PIPE, stderr=PIPE, stdout=PIPE, encoding='utf8', errors='backslashreplace') as process:
            result, error = process.communicate()
        return result, error, process.returncode
        
    async def _run(self):
        
        """Запускает суброцесс в екзекуторе"""
        
        start = datetime.now()
        if self.loop is None:
            loop = asyncio.get_event_loop()
            
        result, error, code = await loop.run_in_executor(self.executor, self._run_subprocess)
        return SubprocessResult(self.command, code, result, error, start, datetime.now())
    
    def __call__(self):
        return self._run()
    
    def ___await__(self):
        return self._run().__await__()
        
    def __del__(self):
        self.executor.shutdown()
        
    def send(self, __value: Any) -> Any:
        return super().send(__value)

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