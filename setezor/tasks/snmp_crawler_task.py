import asyncio
from time import time
import traceback

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from ipaddress import IPv4Address

from setezor.modules.snmp.snmp import SnmpGet



class  SnmpCrawlerTask(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, ip: str, port: int, community_string: str):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.task_id = task_id
        self.db = db

        self.ip = ip
        self.port = port
        self.community_string = community_string

        self._coro = self.run()


    async def _task_func(self):
        # return await SNMP.walk(ip_address=self.ip, port=self.port, community_string=self.community_string)
        data = {}
        snmp_obj = await SnmpGet.create_obj(ip_address=self.ip, port=self.port, community_string=self.community_string)
        data.update({"system" : await snmp_obj.system_name()})
        data.update({"interface_index" : await snmp_obj.interface_index()})
        data.update({"interface_description" : await snmp_obj.interface_description()})
        data.update({"phys_address" : await snmp_obj.phys_address()})
        data.update({"interface_IPs" : await snmp_obj.ip_add_ent_addr()})
        data.update({"interface_IP_indexes" : await snmp_obj.ip_add_ent_if_ind()})
        
        return data


    async def _write_result_to_db(self, data):
        # TODO (add interface objectes (name, mac, speed ...)) ?
        for i in range(len(data.get("interface_IPs", []))):
            if data["interface_IPs"][i] != self.ip:
                new_ip_mac = {"ip": data["interface_IPs"][i],
                              "mac": data["phys_address"][data["interface_index"].index(data["interface_IP_indexes"][i])]}
                if (new_ip_mac.get("mac")):
                    self.db.ip.get_or_create(**new_ip_mac)
                else:
                    self.db.ip.create(**new_ip_mac)


    async def run(self):
        self.db.task.set_pending_status(index=self.task_id)
        try:
            IPv4Address(self.ip)
            if not self.community_string:
                raise Exception("Community string must not be empty")
            start_time = time()
            result = await self._task_func()
            self.logger.debug('Task func "%s" finished after %.2f seconds', self.__class__.__name__, time() - start_time)
            await self._write_result_to_db(data=result)
            self.logger.debug('Result of task "%s" wrote to db', self.__class__.__name__)
        except Exception as e:
            self.logger.error('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            self.db.task.set_failed_status(index=self.task_id, error_message=traceback.format_exc())
            raise e
        self.db.task.set_finished_status(index=self.task_id)