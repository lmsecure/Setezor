from setezor.models.dns import DNS
from setezor.services.base_service import BaseService


class DNS_Service(BaseService):
    async def create(self, dns_model: DNS):
        async with self._uow:
            new_dns = self._uow.dns.add(dns_model.model_dump())
            await self._uow.commit()
            return new_dns

    async def add_dns(self, target_ip_id: str, target_domain_id: str, ip_id: str):
        # TODO: тут target_ip_id становится не обязательным (кроме A и AAAA)
        #       так же требуется аргумент dns_type из from setezor.db.entities import DNSTypes
        #       на данный момент метод не используется
        async with self._uow:
            ip_obj = await self._uow.ip.find_one(id=ip_id)
        new_obj = DNS(target_ip_id=target_ip_id, target_domain_id=target_domain_id, scan_id=ip_obj.scan_id)
        dns_a_obj = await self.create(new_obj)
        return dns_a_obj

    async def get_by_domain_id(self, target_domain_id: str) -> DNS:
         async with self._uow:
            stmt = await self._uow.dns.find_one(target_domain_id=target_domain_id)
            return stmt

    async def delete_by_dns_a_id(self, id: str) -> bool:
         async with self._uow:
            stmt = await self._uow.dns.delete(id=id)
            await self._uow.commit()
            return True