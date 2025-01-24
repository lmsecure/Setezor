from setezor.schemas.dns import DNSSchema,DNSSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class DNSService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, dns: DNSSchemaAdd) -> int:
        dns_dict = dns.model_dump()
        async with uow:
            dns_id = await uow.dns.add(dns_dict)
            await uow.commit()
            return dns_id

    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[DNSSchema]:
        async with uow:
            dns = await uow.dns.list()
            return dns

    @classmethod
    async def get(cls, uow: UnitOfWork, id: int) -> DNSSchema:
        async with uow:
            dns = await uow.dns.find_one(id=id)
            return dns
