from setezor.services.base_service import BaseService
from setezor.models.mac import MAC


class MacService(BaseService):
    async def create(self, mac_model: MAC):
        async with self._uow:
            new_mac = self._uow.mac.add(mac_model.model_dump())
            await self._uow.commit()
            return new_mac