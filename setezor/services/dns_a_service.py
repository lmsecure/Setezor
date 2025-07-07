from setezor.models.dns_a import DNS_A
from setezor.schemas.dns import DNSSchema, DNSSchemaAdd
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class DNS_A_Service(BaseService):
    async def create(self, dns_a_model: DNS_A):
        async with self._uow:
            new_dns_a = self._uow.dns_a.add(dns_a_model.model_dump())
            await self._uow.commit()
            return new_dns_a

    async def add_dns_a(self, target_ip_id: str, target_domain_id: str, ip_id: str):
        async with self._uow:
            ip_obj = await self._uow.ip.find_one(id=ip_id)
        new_obj = DNS_A(target_ip_id=target_ip_id, target_domain_id=target_domain_id, scan_id=ip_obj.scan_id)
        dns_a_obj = await self.create(new_obj)
        return dns_a_obj
    
    async def get_by_domain_id(self, target_domain_id: str) -> DNS_A:
         async with self._uow:
            stmt = await self._uow.dns_a.find_one(target_domain_id=target_domain_id)
            return stmt
         
    async def delete_by_dns_a_id(self, id: str) -> bool:
         async with self._uow:
            stmt = await self._uow.dns_a.delete(id=id)
            await self._uow.commit()
            return True