
from setezor.services.base_service import BaseService
from setezor.schemas.roles import Roles
from setezor.models import Project

class RoleService(BaseService):
    async def get(self, role_id: str) -> Project:
        async with self._uow:
            return await self._uow.role.find_one(id=role_id)
        
    async def list(self):
        async with self._uow:
            roles = await self._uow.role.list()
            return [role for role in roles if role.name != Roles.owner]
        

    async def get_by_name(self, name: str):
        async with self._uow:
            return await self._uow.role.find_one(name=name)