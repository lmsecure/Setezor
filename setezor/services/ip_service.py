from setezor.schemas.ip import IPSchema, IPSchemaAdd
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import IP

class IPService(BaseService):
    async def create(self, ip: IP) -> int:
        ip_dict = ip.model_dump()
        async with self._uow:
            ip = self._uow.ip.add(ip_dict)
            await self._uow.commit()
            return ip

    async def list_ips(self, project_id: str) -> list:
        async with self._uow:
            ips = await self._uow.ip.filter(project_id=project_id)
        uniq_ips = set([item.ip for item in ips if item.scan_id and item.ip])
        result = sorted(uniq_ips, key=lambda item: tuple(map(int, item.split('.'))))
        return result

    async def get_ips_and_ports(self, project_id: str) -> list:
        async with self._uow:
            ips_ports = await self._uow.ip.get_ips_ports(project_id=project_id)
        result = []
        for ip, port in ips_ports:
            result.append({"ip" : ip, "port" : port})
        return sorted(result, key=lambda x: (tuple(map(int, x['ip'].split('.'))), x['port']))

    async def get(self, id: int) -> IPSchema:
        async with self._uow:
            ip = await self._uow.ip.find_one(id=id)
            return ip
        
    async def update_object_type(self, project_id: str, ip_id: str, object_type_id: str):
        async with self._uow:
            ip = await self._uow.ip.find_one(project_id=project_id, id=ip_id)
            mac = await self._uow.mac.find_one(project_id=project_id, id=ip.mac_id)
            object = await self._uow.object.find_one(project_id=project_id, id=mac.object_id)
            await self._uow.object.edit_one(id=object.id, data={"object_type_id" : object_type_id})
            await self._uow.commit()
            return await self._uow.object_type.find_one(id=object_type_id)
        