from .base_job import BaseJob, MessageObserver
from database.queries import Queries
from time import time
import traceback
import asyncio

from .nmap_scan_task import NmapScanTask
from modules.snmp import NmanSnmpParser

from network_structures import IPv4Struct, RouteStruct

class SNMPScanTask(NmapScanTask):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, name: str, task_id: int, command: str, iface: str, nmap_logs: str, db: Queries):
        super().__init__(agent_id, observer, scheduler, name, task_id, command, iface, nmap_logs, db)
    
    async def _task_func(self, arguments: dict, cnmp_log_path: str) -> str:
        #! todo
        ...
    
    
    def _write_result_to_db(self, db: Queries) -> None:
        #! todo
        ...
        
        
    async def run(self, db: Queries, task_id: int, arguments: dict, scanning_ip: str, scanning_mac: str, snmp_log_path: str):
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
        try:
            t1 = time()
            arguments['interface_addr'] = scanning_ip
            result = await self._task_func(arguments=arguments, snmp_log_path=snmp_log_path)
            ports, links = await self._parser_results(format=arguments.get('format', 'oJ'), input_data=result, scanning_ip=address.ip, scanning_mac=address._mac.mac)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, port_result=ports, link_result=links)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)