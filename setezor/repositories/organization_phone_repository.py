from sqlmodel import SQLModel

from setezor.models import Phone
from setezor.repositories import SQLAlchemyRepository


class OrganizationPhoneRepository(SQLAlchemyRepository[Phone]):
    model = Phone

    async def exists(self, org_phone_obj: SQLModel):
        return False