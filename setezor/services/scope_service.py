
from fastapi import HTTPException
from setezor.interfaces.service import IService
from setezor.models import Scope, Target
from setezor.schemas.scope import ScopeCreateForm
from setezor.schemas.target import TargetCreate
from setezor.unit_of_work.unit_of_work import UnitOfWork

from io import StringIO

class ScopeService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, scope: ScopeCreateForm) -> Scope:
        new_scope_model = Scope(
            name=scope.name,
            description=scope.description,
            project_id=project_id
        )
        async with uow:
            new_scope = uow.scope.add(new_scope_model.model_dump())
            await uow.commit()
            return new_scope
        
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            return await uow.scope.project_scopes(project_id=project_id)
        
    @classmethod
    async def get(cls, uow: UnitOfWork, id: str):
        async with uow:
            return await uow.scope.find_one(id=id)
        
    @classmethod
    async def create_targets(cls, uow: UnitOfWork, project_id: str, id: str, payload: TargetCreate):
        
        targets = payload.targets
        result = []
        for target in targets:
            params = target.model_dump()
            if target.ip or target.domain:
                result.append(params)
        async with uow:
            for params in result:
                if params:
                    new_target = Target(
                        project_id=project_id,
                        scope_id=id,
                        **params)
                    if not await uow.target.find_one(**new_target.model_dump()):
                        uow.target.add(new_target.model_dump())
            await uow.commit()
            return await uow.target.for_scope(scope_id=id, project_id=project_id)
    
    @classmethod
    async def get_targets(cls, uow: UnitOfWork, project_id: str, id: str):
        async with uow:
            return await uow.target.for_scope(project_id=project_id, scope_id=id)
        
    @classmethod
    async def delete_scope_by_id(cls, uow: UnitOfWork, id: str):
        async with uow:
            await uow.scope.delete(id=id)
            await uow.commit()
            return True


    @classmethod
    async def get_csv_from_scope(cls, uow: UnitOfWork, project_id: str, scope_id: str) -> bytes:
        async with uow:
            targets = await uow.target.for_scope(project_id=project_id, scope_id=scope_id)
        if not targets:
            raise HTTPException(status_code=204)
        result = StringIO()
        for target in targets:
            result.write(f"{target.protocol or ''},{target.ip or ''},{target.domain or ''},{target.port or ''}\n")
        result.seek(0)
        return result