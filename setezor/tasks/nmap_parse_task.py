import traceback
from time import time
from base64 import b64decode
from setezor.managers.websocket_manager import WS_MANAGER
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.tasks.base_job import BaseJob
from setezor.services import DataStructureService, TasksService
from setezor.schemas.task import TaskStatus, WebSocketMessage
from setezor.modules.nmap.parser import NmapParser
from setezor.modules.nmap.scanner import NmapScanner



class NmapParseTask(BaseJob):
    def __init__(self, uow: UnitOfWork, scheduler, name: str, task_id: str, 
                 project_id: str, 
                 scan_id: str, 
                 agent_id: str, 
                 file: str, filename: str, interface_ip_id: str, mac: str, ip: str):
        super().__init__(scheduler=scheduler, name=name)
        self.uow: UnitOfWork = uow
        self.task_id = task_id
        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.file = file
        self.filename = filename
        self.interface_ip_id = interface_ip_id
        self.mac = mac
        self.ip = ip
        self._coro = self.run()

    async def _task_func(self):
        data = b64decode(self.file.split(',')[1])
        data = NmapScanner.parse_xml(data)
        parse_result = NmapParser().parse_hosts(scan = data.get('nmaprun'), agent_id=self.agent_id, self_address={'ip': self.ip, 'mac': self.mac})
        result = NmapParser.restruct_result(data=parse_result, interface_ip_id=self.interface_ip_id)
        return result

    async def _write_result_to_db(self, result):
        service = DataStructureService(uow=self.uow, 
                                       result=result, 
                                       project_id=self.project_id, 
                                       scan_id=self.scan_id)
        await service.make_magic()
        await TasksService.set_status(uow=self.uow, id=self.task_id, status=TaskStatus.finished, project_id=self.project_id)


    async def run(self):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        try:
            t1 = time()
            result = await self._task_func()
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            await self._write_result_to_db(result=result)
        except Exception as e:
            print('Task "%s" failed with error\n%s',
                  self.__class__.__name__, traceback.format_exc())
            raise e
