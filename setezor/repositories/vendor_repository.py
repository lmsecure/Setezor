from setezor.models import Vendor
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select


class VendorRepository(SQLAlchemyRepository[Vendor]):
    model = Vendor

    async def exists(self, vendor_obj: Vendor):
        if not vendor_obj.name:
            return
        stmt = select(Vendor).filter(Vendor.name == vendor_obj.name)
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj
