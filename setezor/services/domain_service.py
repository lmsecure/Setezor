from setezor.models.domain import Domain
from setezor.schemas.domain import DomainSchema,DomainSchemaAdd
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork


class DomainsService(BaseService):
    async def create(self, domain: Domain) -> int:
        async with self._uow:
            domain = self._uow.domain.add(domain.model_dump())
            await self._uow.commit()
            return domain
    
    async def list_domains(self, project_id: str) -> list:
        async with self._uow:
            domains = await self._uow.domain.filter(project_id=project_id)
            uniq_domains = set([item.domain for item in domains])
            return sorted(uniq_domains)
