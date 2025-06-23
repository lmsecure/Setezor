
from sqlalchemy.orm import aliased
from requests import session
from sqlalchemy import Select, desc, text
from sqlmodel import select, func, or_, and_
from setezor.models import SoftwareVersion
from setezor.models.l4_software import L4Software
from setezor.repositories import SQLAlchemyRepository
from sqlmodel import SQLModel

class SoftwareVersionRepository(SQLAlchemyRepository[SoftwareVersion]):
    model = SoftwareVersion

    async def exists(self, software_version_obj: SoftwareVersion):
        dct = software_version_obj.model_dump()
        filtered_keys = {k:v for k, v in dct.items() if v is not None}
        if not filtered_keys: return False
        stmt = select(SoftwareVersion).filter_by(**filtered_keys)
        res = await self._session.exec(stmt)
        return res.first()