
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Project

class RoleService(IService):
    @classmethod
    async def get(cls, uow: UnitOfWork, role_id: str) -> Project:
        async with uow:
            return await uow.role.find_one(id=role_id)