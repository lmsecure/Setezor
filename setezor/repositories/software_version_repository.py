
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
        if not software_version_obj.cpe23:
            return
        cpe23 = software_version_obj.cpe23
        stmt = select(SoftwareVersion).filter(SoftwareVersion.cpe23 == cpe23)
        result = await self._session.exec(stmt)
        result_obj = result.first()
        return result_obj