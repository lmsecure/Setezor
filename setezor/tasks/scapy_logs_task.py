
import traceback

from time import time
from base64 import b64decode

from setezor.tasks.base_job import BaseJob
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.services import DataStructureService, TasksService
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.managers.websocket_manager import WS_MANAGER

from setezor.modules.sniffing.scapy_parser import ScapyParser



class ScapyLogsTask(BaseJob):

    def __init__(self, uow: UnitOfWork, scheduler, name: str, task_id: int, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: int, file: str):
        super().__init__(scheduler=scheduler, name=name)
        self.uow: UnitOfWork = uow
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.file = file
        self._coro = self.run()


    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        return ScapyParser.parse_logs(data = data)


    async def _write_result_to_db(self, result):
        service = DataStructureService(uow=self.uow, 
                                       result=result, 
                                       project_id=self.project_id, 
                                       scan_id=self.scan_id)
        await service.make_magic()
        await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.finished, project_id=self.project_id)


    async def run(self):
        try:
            t1 = time()
            pkt_list = await self._task_func()
            result = ScapyParser.restruct_result(data=pkt_list, agent_id=self.agent_id)
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            await self._write_result_to_db(result=result)
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e