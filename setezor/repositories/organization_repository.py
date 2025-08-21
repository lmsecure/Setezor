from sqlmodel import SQLModel

from setezor.models import Organization
from setezor.repositories import SQLAlchemyRepository


class OrganizationRepository(SQLAlchemyRepository[Organization]):
    model = Organization

    async def exists(self, org_obj: SQLModel):
        return False