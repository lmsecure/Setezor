
from setezor.services.base_service import BaseService
from setezor.models import Target
from setezor.schemas.target import TargetCreate, TargetCreateForm
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List, Dict


class TargetService(BaseService):
    async def create(self, project_id: str, target: TargetCreateForm) -> Target:
        new_target_model = Target(
            **target.model_dump(),
            project_id=project_id
        )
        async with self._uow:
            new_target = self._uow.target.add(new_target_model.model_dump())
            await self._uow.commit()
            return new_target
        
    async def list(self, project_id: str):
        async with self._uow:
            return await self._uow.target.filter(project_id=project_id)
        
    async def get(self, id: str):
        async with self._uow:
            return await self._uow.target.find_one(id=id)

    async def delete_target_by_id(self, target_id: str):
        async with self._uow:
            await self._uow.target.delete(id=target_id)
            await self._uow.commit()
        return
    
    async def update_target_by_id(self, target_id: str, updated_data: TargetCreate):
        async with self._uow:
            await self._uow.target.edit_one(id=target_id, data=updated_data.model_dump())
            await self._uow.commit()