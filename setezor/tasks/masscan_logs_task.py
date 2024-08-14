from .base_job import BaseJob, MessageObserver
from setezor.modules.masscan.executor import MasscanScanner
from setezor.modules.masscan.parser import XMLParser, JsonParser, ListParser, BaseMasscanParser, PortStructure, NetworkLink
from .masscan_scan_task import MasscanScanTask
from setezor.database.queries import Queries
from time import time
import traceback
import asyncio
from typing import Dict, Type, List, Tuple

class MasscanJSONLogTask(MasscanScanTask):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, name: str, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str, db: Queries):
        super(MasscanScanTask, self).__init__(agent_id = agent_id, observer = observer, scheduler = scheduler, name = name)
        self._coro = self.run(db=db, task_id=task_id, input_data=input_data, scanning_ip=scanning_ip, scanning_mac=scanning_mac, masscan_log_path=masscan_log_path)
    
    async def run(self, db: Queries, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str):
        """Метод выполнения задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        ses = db.db.create_session()
        agent = db.agent.get_by_id(session=ses, id=self.agent_id)
        address = agent.ip
        try:
            t1 = time()
            await MasscanScanner.save_source_data(path=masscan_log_path, source_data=input_data, command=self.__class__.__name__.lower(), extension='json')
            ports, links = await self._parser_results(format='oJ', input_data=input_data, scanning_ip=address.ip, scanning_mac=address._mac.mac)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, port_result=ports, link_result=links)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
        
class MasscanXMLLogTask(MasscanScanTask):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, name: str, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str, db: Queries):
        super(MasscanScanTask, self).__init__(agent_id, observer, scheduler, name)
        self._coro = self.run(db=db, task_id=task_id, input_data=input_data, scanning_ip=scanning_ip, scanning_mac=scanning_mac, masscan_log_path=masscan_log_path)
    
    async def run(self, db: Queries, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str):
        """Метод выполнения задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        try:
            t1 = time()
            await MasscanScanner.save_source_data(path=masscan_log_path, source_data=input_data, command=self.__class__.__name__.lower(), extension='xml')
            ports, links = await self._parser_results(format='oX', input_data=input_data, scanning_ip=scanning_ip, scanning_mac=scanning_mac)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, port_result=ports, link_result=links)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
        
        
class MasscanListLogTask(MasscanScanTask):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, name: str, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str, db: Queries):
        super(MasscanScanTask, self).__init__(agent_id, observer, scheduler, name)
        self._coro = self.run(db=db, task_id=task_id, input_data=input_data, scanning_ip=scanning_ip, scanning_mac=scanning_mac, masscan_log_path=masscan_log_path)
    
    async def run(self, db: Queries, task_id: int, input_data: dict, scanning_ip: str, scanning_mac: str, masscan_log_path: str):
        """Метод выполнения задачи

        Args:
            db (Queries): объект запросов к базе
            task_id (int): идентификатор задачи
        """
        db.task.set_pending_status(index=task_id)
        try:
            t1 = time()
            await MasscanScanner.save_source_data(path=masscan_log_path, source_data=input_data, command=self.__class__.__name__.lower(), extension='list')
            ports, links = await self._parser_results(format='oL', input_data=input_data, scanning_ip=scanning_ip, scanning_mac=scanning_mac)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, port_result=ports, link_result=links)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)