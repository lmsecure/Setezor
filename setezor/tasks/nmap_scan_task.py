import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver
from setezor.modules.nmap.scanner import NmapScanner
from setezor.modules.nmap.parser import NmapParser
from setezor.tools.ip_tools import get_ipv4, get_mac
from setezor.database.queries import Queries

from setezor.network_structures import AnyIPAddress, IPv4Struct, PortStruct
from setezor.modules.nmap.parser import NmapRunResult, NmapStructure
from setezor.spy import spy


class NmapScanTask(BaseJob):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, 
                 name: str, task_id: int, command: str, 
                 iface: str, nmap_logs: str, db: Queries):
        super().__init__(agent_id = agent_id, observer = observer, scheduler = scheduler, name = name)
        self.agent_id = agent_id
        self.task_id = task_id
        self._coro = self.run(db=db, task_id=task_id, command=command, iface=iface, nmap_logs=nmap_logs)
    
    @spy.spy_method
    @staticmethod
    async def _task_func(command: str, iface: str, agent_id: int, nmap_logs: str, address: IPv4Struct | dict = {}) -> NmapStructure:
        """Запускает активное сканирование с использованием nmap-а

        Args:
            command (str): параметры сканирования
            _password (str): пароль супер пользователя для некоторых параметров

        Returns:
            _type_: результат сканирования
        """
        loop = asyncio.get_event_loop()
        cmd = ' '.join(command.split(' '))
        cmd += f' -e {iface}'
        scan_result = await NmapScanner().async_run(extra_args=cmd, _password=None, logs_path=nmap_logs)
        return await loop.run_in_executor(None, NmapParser().parse_hosts, scan_result.get('nmaprun'), agent_id, address)
    
    def _write_result_to_db(self, db: Queries, result: NmapStructure):
        """Метод парсинга результатов сканирования nmap-а и занесения в базу

        Args:
            db (Queries): объект запросов в базу
            result (list): результат сканирования nmap-а
            iface (str): имя сетевого интерфейса
        # """

        db.ip.write_many(data=result.addresses)
        db.port.write_many(data=result.ports)
        db.software.write_many(data=result.softwares, to_update=False)
        for port, soft in zip(result.ports, result.softwares):
            if any([v for k, v in soft.items() if k not in ['ip', 'port']]):
                db.resource_software.get_or_create(**{**port, **soft})
        for rt in result.traces:
            db.route.create(route=rt, task_id=self.task_id)
        
    async def run(self, db: Queries, task_id: int, command: str, iface: str, nmap_logs: str):
        """Метод выполнения задачи
        1. Произвести операции согласно методу self._task_func
        2. Записать результаты в базу согласно методу self._write_result_to_db
        3. Попутно менять статут задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        ses = db.db.create_session()
        agent = db.agent.get_by_id(session=ses, id=self.agent_id)
        address = agent.ip
        address = {'ip': address.ip, 'mac': address._mac.mac}
        try:
            t1 = time()
            ip, port = db.agent.get_ip_port(agent_id=self.agent_id)
            result = await self._task_func.run_on_agent(ip, port, command=command, iface=iface, agent_id=self.agent_id, nmap_logs=nmap_logs, address=address)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)