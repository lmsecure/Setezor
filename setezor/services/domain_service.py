from setezor.schemas.domain import DomainSchema,DomainSchemaAdd
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork


class DomainsService(IService):

    @classmethod
    async def list_domains(cls, uow: UnitOfWork, project_id: str) -> list:
        async with uow:
            domains = await uow.domain.filter(project_id=project_id)
            uniq_domains = set([item.domain for item in domains])
            return sorted(uniq_domains)
