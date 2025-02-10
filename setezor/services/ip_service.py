from setezor.schemas.ip import IPSchema, IPSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List
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
    async def list(cls, uow: UnitOfWork) -> List[IPSchema]:
        async with uow:
            ips = await uow.ip.list()
            return ips

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> IPSchema:
        async with uow:
            ip = await uow.ip.find_one(id=id)
            return ip
