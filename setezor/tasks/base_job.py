import asyncio
from abc import abstractmethod
import base64
from aiojobs._job import Job
from aiojobs._scheduler import Scheduler
import aiohttp
import pickle
from setezor.spy import Spy
from setezor.managers import agent_manager as AM, cipher_manager as CM

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

    async def _start(self):
        return super()._start()

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

    async def send_result_to_parent_agent(self, result):
        data = pickle.dumps(result)
        b64encoded_entities = base64.b64encode(data).decode()
        result = {
            "signal": "result_entities",
            "task_id": self.task_id,
            "entities": b64encoded_entities
        }
        ciphered_data = AM.AgentManager.single_cipher(key=Spy.SECRET_KEY, data=result).decode()
        data_for_parent_agent = {
            "sender": self.agent_id,
            "data": ciphered_data
        }
        url = f"{Spy.PARENT_AGENT_URL}/api/v1/agents/backward"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data_for_parent_agent, ssl=False) as resp:
                return resp.status


class CustomScheduler(Scheduler):
    async def spawn_job(self, job: BaseJob) -> Job:
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        # should_start = self._limit is None or self.active_count < self._limit
        # if should_start:
        #     await job._start()
        # else:
        #     try:
        #         await self._pending.put(job)
        #     except asyncio.CancelledError:
        #         await job.close()
        #         raise
        try:
            await self._pending.put(job)
        except asyncio.CancelledError:
            await job.close()
            raise
        self._jobs.add(job)
        return job

    @property
    def jobs(self):
        return self._jobs