
from fastapi import HTTPException
from setezor.services.base_service import BaseService
from setezor.models import Scope, Target
from setezor.schemas.scope import ScopeCreateForm
from setezor.schemas.target import TargetCreate
from setezor.unit_of_work.unit_of_work import UnitOfWork

from io import StringIO

class ScopeService(BaseService):
    async def create(self, project_id: str, scope: ScopeCreateForm) -> Scope:
        new_scope_model = Scope(
            name=scope.name,
            description=scope.description,
            project_id=project_id
        )
        async with self._uow:
            new_scope = self._uow.scope.add(new_scope_model.model_dump())
            await self._uow.commit()
            return new_scope
        
    async def list(self, project_id: str):
        async with self._uow:
            return await self._uow.scope.project_scopes(project_id=project_id)
        
    async def get(self, id: str):
        async with self._uow:
            return await self._uow.scope.find_one(id=id)
        
    async def create_targets(self, project_id: str, id: str, payload: TargetCreate):
        
        targets = payload.targets
        result = []

        for target in targets:
            if not (target.ip or target.domain):
                raise HTTPException(
                    status_code=400,
                    detail="Each target must have at least 'ip' or 'domain'"
                )
            params = target.model_dump()
            if target.ip or target.domain:
                result.append(params)
        async with self._uow:
            for params in result:
                if params:
                    new_target = Target(
                        project_id=project_id,
                        scope_id=id,
                        **params)
                    if not await self._uow.target.find_one(**new_target.model_dump()):
                        self._uow.target.add(new_target.model_dump())
            await self._uow.commit()
            return await self._uow.target.for_scope(scope_id=id, project_id=project_id)
    
    async def get_targets(self, project_id: str, id: str):
        async with self._uow:
            return await self._uow.target.for_scope(project_id=project_id, scope_id=id)
        
    async def get_filtred_targets(self, project_id: str, id: str, page: int = 1, limit: int = 50):
        async with self._uow:
            return await self._uow.target.for_scope_filtred(
                project_id=project_id, 
                scope_id=id,
                page=page,
                limit=limit
            )
        
    async def delete_scope_by_id(self, id: str):
        async with self._uow:
            await self._uow.scope.delete(id=id)
            await self._uow.commit()
            return True


    async def get_csv_from_scope(self, project_id: str, scope_id: str) -> bytes:
        async with self._uow:
            targets = await self._uow.target.for_scope(project_id=project_id, scope_id=scope_id)
        if not targets:
            raise HTTPException(status_code=204)
        result = StringIO()
        for target in targets:
            result.write(f"{target.protocol or ''},{target.ip or ''},{target.domain or ''},{target.port or ''}\n")
        result.seek(0)
        return result