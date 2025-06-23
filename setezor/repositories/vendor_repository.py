from setezor.models import Vendor
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel, select


class VendorRepository(SQLAlchemyRepository[Vendor]):
    model = Vendor

    async def exists(self, vendor_obj: Vendor):
        stmt = select(Vendor).filter(Vendor.name == vendor_obj.name)
        res = await self._session.exec(stmt)
        return res.first()
