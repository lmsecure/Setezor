from setezor.models import Vendor
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select

class VendorRepository(SQLAlchemyRepository[Vendor]):
    model = Vendor


    async def exists(self, vendor_obj: Vendor):
        dct = vendor_obj.model_dump()
        filtered_keys = {k:v for k, v in dct.items() if v}
        filtered_keys["name"] = vendor_obj.name
        if not filtered_keys: return False
        stmt = select(Vendor).filter_by(**filtered_keys)
        res = await self._session.exec(stmt)
        return res.first()