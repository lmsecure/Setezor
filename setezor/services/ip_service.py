from setezor.schemas.ip import IPSchema, IPSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import IP

class IPService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, ip: IP) -> int:
        ip_dict = ip.model_dump()
        async with uow:
            ip = uow.ip.add(ip_dict)
            await uow.commit()
            return ip

    @classmethod
    async def list_ips(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            ips = await uow.ip.filter(project_id=project_id)
        uniq_ips = set([item.ip for item in ips if item.scan_id and item.ip])
        result = sorted(uniq_ips, key=lambda item: tuple(map(int, item.split('.'))))
        return result

    @classmethod
    async def get_ips_and_ports(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            ips_ports = await uow.ip.get_ips_ports(project_id=project_id)
        result = []
        for ip, port in ips_ports:
            result.append({"ip" : ip, "port" : port})
        return sorted(result, key=lambda x: (tuple(map(int, x['ip'].split('.'))), x['port']))

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> IPSchema:
        async with uow:
            ip = await uow.ip.find_one(id=id)
            return ip
        
    @classmethod
    async def update_object_type(cls, uow: UnitOfWork, project_id: str, ip_id: str, object_type_id: str):
        async with uow:
            ip = await uow.ip.find_one(project_id=project_id, id=ip_id)
            mac = await uow.mac.find_one(project_id=project_id, id=ip.mac_id)
            object = await uow.object.find_one(project_id=project_id, id=mac.object_id)
            await uow.object.edit_one(id=object.id, data={"object_type_id" : object_type_id})
            await uow.commit()
            return await uow.object_type.find_one(id=object_type_id)
        