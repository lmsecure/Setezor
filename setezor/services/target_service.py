
from setezor.interfaces.service import IService
from setezor.models import Target
from setezor.schemas.target import TargetCreate, TargetCreateForm
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List, Dict


class TargetService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, target: TargetCreateForm) -> Target:
        new_target_model = Target(
            **target.model_dump(),
            project_id=project_id
        )
        async with uow:
            new_target = uow.target.add(new_target_model.model_dump())
            await uow.commit()
            return new_target
        
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            return await uow.target.filter(project_id=project_id)
        
    @classmethod
    async def get(cls, uow: UnitOfWork, id: str):
        async with uow:
            return await uow.target.find_one(id=id)
        
    @classmethod
    async def get_transform_cert_scope_data(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            scope_cert_data = await uow.target.get_cert_scope_data(project_id=project_id)
            result = [
                {"target": row[1], "port": row[2]} if row[1] is not None else {"target": row[1], "port": row[2]}
                for row in scope_cert_data
            ]
            return result
        
    @classmethod
    async def delete_target_by_id(cls, uow: UnitOfWork, target_id: str):
        async with uow:
            await uow.target.delete(id=target_id)
            await uow.commit()
        return
    
    @classmethod
    async def update_target_by_id(cls, uow: UnitOfWork, target_id: str, updated_data: TargetCreate):
        async with uow:
            await uow.target.edit_one(id=target_id, data=updated_data.model_dump())
            await uow.commit()