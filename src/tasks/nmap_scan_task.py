import traceback
import asyncio
from time import time

from .base_job import BaseJob, MessageObserver

from modules.nmap.scanner import NmapScanner
from modules.nmap.parser import NmapParser, NmapStructure
from tools.ip_tools import get_ipv4, get_mac
from database.queries import Queries

from network_structures import AnyIPAddress, IPv4Struct, PortStruct

    
class NmapScanTask(BaseJob):
    
    def __init__(self, agent_id: int, observer: MessageObserver, scheduler, 
                 name: str, task_id: int, command: str, 
                 iface: str, nmap_logs: str, db: Queries):
        super().__init__(agent_id, observer, scheduler, name)
        self.agent_id = agent_id
        self.task_id = task_id
        self._coro = self.run(db=db, task_id=task_id, command=command, iface=iface, nmap_logs=nmap_logs)
    
    async def _task_func(self, command: str, iface: str, nmap_logs: str, address: AnyIPAddress | dict = {}):
        """Запускает активное сканирование с использованием nmap-а

        Args:
            command (str): параметры сканирования
            _password (str): пароль супер пользователя для некоторых параметров

        Returns:
            _type_: результат сканирования
        """
        loop = asyncio.get_event_loop()
        cmd = command + f' -e {iface}'
        scan_result = await NmapScanner().async_run(extra_args=cmd, _password=None, logs_path=nmap_logs)
        return await loop.run_in_executor(None, NmapParser().parse_hosts, scan_result.get('nmaprun'), self.agent_id, address)
    
    def _write_result_to_db(self, db: Queries, result: NmapStructure):
        """Метод парсинга результатов сканирования nmap-а и занесения в базу

        Args:
            db (Queries): объект запросов в базу
            result (list): результат сканирования nmap-а
            iface (str): имя сетевого интерфейса
        # """

        db.ip.write_many(data=result.addresses)
        db.port.write_many(data=result.ports)
        for rt in result.traces:
            db.route.create(route=rt, task_id=self.task_id)
        # Всратый код ниже достает все ip из traces и address, чтобы в дальнейшем создать подсети
        # all_addresses = {}
        # for trace in result.traces:
        #     if trace['parent_ip']:
        #         ip = all_addresses.get(trace['parent_ip'])
        #         if ip:
        #             ip.update({'mac': ip.get('parent_mac'), 'domain': ip.get('parent_name')})
        #         else:
        #             ip = {'mac': trace['parent_mac'], 'domain': trace['parent_name']}
        #             all_addresses[trace['parent_ip']] = ip
        #     if trace['child_ip']:
        #         ip = all_addresses.get(trace['child_ip'])
        #         if ip:
        #             ip.update({'mac': ip['child_mac'], 'domain': ip['child_name']})
        #         else:
        #             ip = {'mac': trace['child_mac'], 'domain': trace['child_name']}
        #             all_addresses[trace['child_ip']] = ip
        # if result.traces:
        #     ip = all_addresses.get(result.traces[0]['start_ip'])
        #     if not ip:
        #         all_addresses[result.traces[0]['start_ip']] = {}
        
        # for addr in result.addresses:
        #     ip = all_addresses.get(addr['ip'])
        #     if ip:
        #         ip.update({'domain': ip.get('domain')})
        #     else:
        #         ip = {addr['ip']: {'domain': addr.get('domain_name')}}
        # res = []
        # for key, value in all_addresses.items():
        #     value.update({'ip': key})
        #     res.append(value)
        # db.network.create_from_addresses(addresses=[IPv4Struct.model_validate(i) for i in res])
        
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
            result = await self._task_func(command=command, iface=iface, nmap_logs=nmap_logs, address=address)
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)