from setezor.services.base_service import BaseService
from setezor.models.network import Network


class NetworkService(BaseService):
    async def create(self, network_model: Network):
        async with self._uow:
            new_network = self._uow.network.add(network_model.model_dump())
            await self._uow.commit()
            return new_network