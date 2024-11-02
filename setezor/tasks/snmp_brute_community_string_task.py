import asyncio
from time import time
import traceback

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from ipaddress import IPv4Address

from setezor.modules.snmp.snmp import SNMP, SnmpGettingAccess


class  SnmpBruteCommunityStringTask(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, ip: str, port: int, community_strings: list):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.task_id = task_id
        self.db = db
        self.ip = ip
        self.port = port
        self.community_strings = community_strings
        self._coro = self.run()

    async def _task_func(self):
        return  await SnmpGettingAccess.community_string(ip_address=self.ip, port=self.port, community_strings=self.community_strings)

    async def _write_result_to_db(self, data):
        resource = {"port" : 161, "ip" : self.ip}
        obj_resource = self.db.resource.get_or_create(**resource)
        for d in data:
            permission = 0
            if not d[2]:
                permission += 1
                if await SnmpGettingAccess.is_write_access(ip_address=self.ip, port=self.port, community_string=d[1]):
                    permission += 2
            result = {"resource_id": obj_resource.id,
                      "login": d[1],
                      "need_auth": d[2] == "authorizationError",
                      "permissions" : permission}
            self.db.authentication_credentials.get_or_create(**result)

    async def run(self):
        self.db.task.set_pending_status(index=self.task_id)
        try:
            IPv4Address(self.ip)
            start_time = time()
            result = await self._task_func()
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - start_time)
            if result:
                await self._write_result_to_db(data=result)
                self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
            else:
                self.observer.notify({'title': f'Task "{self.name}"', 'text': f"Community string not found", 'type': 'warning'}, 'message')
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            self.db.task.set_failed_status(index=self.task_id, error_message=traceback.format_exc())
            raise e
        self.db.task.set_finished_status(index=self.task_id)