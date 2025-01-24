
from base64 import b64decode
import csv
import io

from setezor.interfaces.service import IService
from setezor.models import Scope, Target
from setezor.schemas.scope import ScopeCreateForm
from setezor.schemas.target import TargetCreate
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class ScopeService(IService):
    @classmethod
    async def create(cls, uow: UnitOfWork, project_id: str, scope: ScopeCreateForm) -> Scope:
        new_scope_model = Scope(
            name=scope.name,
            description=scope.description,
            project_id=project_id
        )
        async with uow:
            new_scope = await uow.scope.add(new_scope_model.model_dump())
            await uow.commit()
            return new_scope
        
    @classmethod
    async def list(cls, uow: UnitOfWork, project_id: str):
        async with uow:
            return await uow.scope.filter(project_id=project_id)
        
    @classmethod
    async def get(cls, uow: UnitOfWork, id: str):
        async with uow:
            return await uow.scope.find_one(id=id)
        
    @classmethod
    async def create_targets(cls, uow: UnitOfWork, project_id: str, id: str, payload: TargetCreate):
        
        targets = payload.targets
        result = []
        if isinstance(targets, str):
            data = b64decode(targets.split(',')[1])
            data = io.BytesIO(data)
            data = io.TextIOWrapper(data, newline='\n')
            data = csv.reader(data)
            for row in data:
                params = {}
                if row:
                    protocol, ip, domain, port = row + [None] * (4 - len(row))
                    if protocol: params.update({"protocol" : protocol})
                    if ip: params.update({"ip" : ip})
                    if domain: params.update({"domain" : domain})
                    if port: params.update({"port" : int(port)})
                    if params:
                        result.append(params)
        else:
            for params in targets:
                params = params.model_dump()
                if any(params.values()):
                    result.append(params)
        async with uow:
            for params in result:
                if params:
                    new_target = Target(
                        project_id=project_id,
                        scope_id=id,
                        **params )
                    await uow.target.add(new_target.model_dump())
                await uow.commit()
            return await uow.target.filter(scope_id=id, project_id=project_id)
    
    @classmethod
    async def get_targets(cls, uow: UnitOfWork, project_id: str, id: str):
        async with uow:
            return await uow.target.filter(project_id=project_id, scope_id=id)