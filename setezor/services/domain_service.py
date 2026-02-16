from setezor.models.domain import Domain
from setezor.schemas.domain import DomainSchema,DomainSchemaAdd
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork


class DomainsService(BaseService):
    async def create(self, domain: Domain) -> Domain:
        async with self._uow:
            domain = self._uow.domain.add(domain.model_dump())
            await self._uow.commit()
            return domain
    
    async def list_domains(self, project_id: str) -> list:
        async with self._uow:
            domains = await self._uow.domain.filter(project_id=project_id)
            uniq_domains = set([item.domain for item in domains])
            return sorted(uniq_domains)

    async def add_domain(self, project_id: str, domain: str, ip_id: str):
            async with self._uow:
                ip_obj = await self._uow.ip.find_one(id=ip_id)
            new_obj = Domain(project_id=project_id, scan_id=ip_obj.scan_id, domain=domain)
            domain_obj = await self.create(new_obj)
            return domain_obj
    
    async def delete_by_domain_id(self, id: str) -> bool:
        async with self._uow:
            stmt = await self._uow.domain.delete(id=id)
            await self._uow.commit()
            return True
        
    async def update_by_domain_id(self, id: str, domain: str) -> bool:
        async with self._uow:
            stmt = await self._uow.domain.edit_one(id=id, data=domain)
            await self._uow.commit()