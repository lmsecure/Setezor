import asyncio
from time import time
import traceback

from .base_job import BaseJob, MessageObserver
from setezor.database.queries import Queries
from ipaddress import IPv4Address, IPv4Network, ip_network

from setezor.modules.snmp.snmp import SnmpGet



class  SnmpCrawlerTask(BaseJob):
    
    def __init__(self, observer: MessageObserver, scheduler, name: str, task_id: int, db: Queries, agent_id: int, ip: str, port: int, snmp_version: int, community_string: str):
        super().__init__(observer = observer, scheduler = scheduler, name = name)
        self.task_id = task_id
        self.db = db

        self.agent_id = agent_id
        self.ip = ip
        self.port = port
        self.snmp_version = snmp_version
        self.community_string = community_string

        self._coro = self.run()


    async def _task_func(self):
        data = {}
        snmp_obj = await SnmpGet.create_obj(ip_address=self.ip, port=self.port, community_string=self.community_string, snmp_version=self.snmp_version)
        data.update({"system" : await snmp_obj.system_name()})
        data.update({"interface_index" : await snmp_obj.interface_index()})
        data.update({"interface_description" : await snmp_obj.interface_description()})
        data.update({"interface_speed" : [s // 1_000_000 for s in await snmp_obj.interface_speed()]})
        data.update({"interface_phys_address" : await snmp_obj.interface_phys_address()})
        data.update({"interface_IPs" : await snmp_obj.ip_ad_ent_addr()})
        data.update({"interface_IP_indexes" : await snmp_obj.ip_add_ent_if_ind()})
        data.update({"interface_IP_masks" : await snmp_obj.ip_ad_ent_net_mask()})
        for i in range(len(data.get("interface_IPs", []))):
            if data["interface_IPs"][i] != self.ip:
                data.update({data["interface_IPs"][i] + "ports" : await snmp_obj.udp_local_ports(data["interface_IPs"][i])})
        data.update({"ip_net_to_media_net_address" : await snmp_obj.ip_net_to_media_net_address()})
        data.update({"ip_net_to_media_phys_address" : await snmp_obj.ip_net_to_media_phys_address()})

        return data


    async def _write_result_to_db(self, data):

        self_ip_obj = self.db.ip.get_by_ip(ip=self.ip)
        if self.ip in data.get("interface_IPs", []) and not self_ip_obj._mac.mac:
            self.db.mac.update_by_id(id = self_ip_obj.mac, to_update={"mac" : data["interface_phys_address"][data["interface_index"].index(data["interface_IP_indexes"][data["interface_IPs"].index(self.ip)])]} )
        self_ip_obj = self.db.ip.get_by_ip(ip=self.ip)

        exist_routes = self.db.route.get_routes_by_ipid_on_start_position(ip_id=self_ip_obj.id)
        interfaces_ips = set()      # уже существующие в базе ip интерфейсов принадлежащие self.ip (сканируемуму узлу)
        subnet_ips = set()          # уже существующие в базе ip подсети (arp таблицы) принадлежащие self.ip (сканируемуму узлу)
        for r in exist_routes:
            if len(r) > 1:
                tmp_if_ip = self.db.ip.get_by_id(id=r[1]).get("ip")
                tmp_sub_ip = self.db.ip.get_by_id(id=r[-1]).get("ip")
                interfaces_ips.add(tmp_if_ip)
                subnet_ips.add(tmp_sub_ip)

        new_routes = []
        for i in range(len(data.get("interface_IPs"))):
            new_route = [self_ip_obj.id]
            mask = IPv4Network('0.0.0.0/' + data["interface_IP_masks"][i]).prefixlen

            if data["interface_IPs"][i] != self.ip and data["interface_IPs"][i] not in interfaces_ips:
                ip_obj_on_if = self.db.ip.create(ip = data["interface_IPs"][i],
                                                 mask=mask,
                                                 type_id=1,
                                                 mac=data["interface_phys_address"][data["interface_index"].index(data["interface_IP_indexes"][i])], 
                                                 interface_name=data["interface_description"][data["interface_index"].index(data["interface_IP_indexes"][i])],
                                                 interface_speed=data["interface_speed"][data["interface_index"].index(data["interface_IP_indexes"][i])])
                new_route.append(ip_obj_on_if.id)
                
            no_ip_in_subnet = True
            for j in range(len(data.get("ip_net_to_media_net_address"))):
                if data["ip_net_to_media_net_address"][j] and data["ip_net_to_media_net_address"][j] != self.ip and data["ip_net_to_media_net_address"][j] != data["interface_IPs"][i] and data["ip_net_to_media_net_address"][j] not in subnet_ips:
                    if IPv4Address(data["ip_net_to_media_net_address"][j]) in ip_network(data["interface_IPs"][i] + '/' + str(mask), strict=False):
                        ip_obj_in_subnet = self.db.ip.create(ip=data["ip_net_to_media_net_address"][j], mask=mask, mac=data["ip_net_to_media_phys_address"][j])
                        new_routes.append(new_route + [ip_obj_in_subnet.id])
            if no_ip_in_subnet and len(new_route) > 1:
                new_routes.append(new_route)
        
        for route in new_routes:
            self.db.route.create_by_ipid(agent_id=self.agent_id, ip_obj_lst=route, task_id=None)


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