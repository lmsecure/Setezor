from setezor.models import ObjectType
from setezor.services.base_service import BaseService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from typing import List


class ObjectTypeService(BaseService):
    async def list(self) -> List[ObjectType]:
        async with self._uow:
            object_types = await self._uow.object_type.list()
            return object_types

