from setezor.services.base_service import BaseService
from setezor.models.asn import ASN


class AsnService(BaseService):
    async def create(self, asn_model: ASN):
        async with self._uow:
            new_asn = self._uow.asn.add(asn_model.model_dump())
            await self._uow.commit()
            return new_asn