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
