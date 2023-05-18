from .base_job import BaseJob, MessageObserver
from modules.nmap.scanner import NmapScanner
from modules.nmap.parser import NmapParser
from tools.ip_tools import get_self_ip
from database.queries import Queries
from time import time
import traceback
import asyncio


class NmapScanTask(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, command: str, iface: str, nmap_logs: str, db: Queries):
        super().__init__(observer, scheduler, name)
        self._coro = self.run(db=db, task_id=task_id, command=command, iface=iface, nmap_logs=nmap_logs)
    
    async def _task_func(self, command: str, iface: str, nmap_logs: str):
        """Запускает активное сканирование с использованием nmap-а

        Args:
            command (str): параметры сканирования
            _password (str): пароль супер пользователя для некоторых параметров

        Returns:
            _type_: результат сканирования
        """
        loop = asyncio.get_event_loop()
        scan_result = await NmapScanner().async_run(extra_args=' '.join(command.split(' ')), _password=None, logs_path=nmap_logs)
        return await loop.run_in_executor(None, NmapParser().parse_hosts, scan_result.get('nmaprun'), get_self_ip(iface))
    
    def _write_result_to_db(self, db: Queries, result):
        """Метод парсинга результатов сканирования nmap-а и занесения в базу

        Args:
            db (Queries): объект запросов в базу
            result (list): результат скаинрования nmap-а
            iface (str): имя сетевого интерфейса
        """
        db.ip.write_many(data=result.addresses)
        db.l3link.write_many(data=result.traces)
        db.port.write_many(data=result.ports)
        
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
        try:
            t1 = time()
            result = await self._task_func(command=command, iface=iface, nmap_logs=nmap_logs)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)