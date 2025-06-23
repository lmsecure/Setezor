from setezor.services.base_service import BaseService
from setezor.models.object import Object


class ObjectService(BaseService):
    async def create(self, object_model: Object):
        async with self._uow:
            new_object = self._uow.object.add(object_model.model_dump())
            await self._uow.commit()
            return new_object