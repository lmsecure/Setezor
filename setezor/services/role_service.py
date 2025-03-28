
from setezor.interfaces.service import IService
from setezor.schemas.roles import Roles
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models import Project

class RoleService(IService):
    @classmethod
    async def get(cls, uow: UnitOfWork, role_id: str) -> Project:
        async with uow:
            return await uow.role.find_one(id=role_id)
        
    @classmethod
    async def list(cls, uow: UnitOfWork):
        async with uow:
            roles = await uow.role.list()
            return [role for role in roles if role.name != Roles.owner]