from setezor.models import ObjectType
from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class ObjectTypeService(IService):
    @classmethod
    async def list(cls, uow: UnitOfWork) -> List[ObjectType]:
        async with uow:
            object_types = await uow.object_type.list()
            return object_types

