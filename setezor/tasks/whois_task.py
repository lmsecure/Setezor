import traceback
import asyncio
from time import time
from .base_job import BaseJob, MessageObserver
from setezor.modules.osint.whois.whoistest import Whois
from setezor.database.queries import Queries
from setezor.tools import ip_tools

class WhoisTask(BaseJob):
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, target: str):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.target = target
        self._coro = self.run(db=db, task_id=task_id, target=target)

    async def _task_func(self, target: str):

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, Whois.get_whois, target)

    def _write_result_to_db(self, db: Queries, result, target):
        data = dict()
        if ip_tools.is_ip_address(self.target):
            data.update({'ip': self.target})
        else:
            data.update({'domain': self.target})
        data.update({'data': result,
                     'domain_crt': result.get('domain', target),
                     'org_name': result.get('org', ''),
                     'AS': '',
                     'range_ip': '',
                     'netmask': ''})
        alias_org_name = ['OrgName', 'Organization', 'organization']
        alias_range = ['NetRange', 'inetnum']
        alias_netmask = ['CIDR', 'route']
        alias_origin = ['OriginAS', 'origin']
        for org_name in alias_org_name:
            if org_name in result:
                data.update({'org_name': result[org_name]})
                break
        for _origin in alias_origin:
            if _origin in result:
                data.update({'AS': result[_origin]})
                break
        for _range in alias_range:
            if _range in result:
                data.update({'range_ip': ", ".join(result[_range])})
                break
        for _net_mask in alias_netmask:
            if _net_mask in result:
                # _netmask = result[i].split('/')[1]
                #print(_net_mask)
                break
        db.whois.get_or_create(**data)

    async def run(self, db: Queries, task_id: int, target: str):
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
            result = await self._task_func(target=target)
            # TODO 
            # if not result:
            #     notify
            self.logger.debug('Task func "%s" finished after %.2f seconds',
                              self.__class__.__name__, time() - t1)
            self._write_result_to_db(db=db, result=result, target=target)
            self.logger.debug('Result of task "%s" wrote to db',
                              self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s',
                              self.__class__.__name__, traceback.format_exc())
            db.task.set_failed_status(
                index=task_id, error_message=traceback.format_exc())
            raise e
        db.task.set_finished_status(index=task_id)
