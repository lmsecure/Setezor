from sqlmodel import SQLModel

from setezor.models import Email
from setezor.repositories import SQLAlchemyRepository


class OrganizationEmailRepository(SQLAlchemyRepository[Email]):
    model = Email

    async def exists(self, org_email_obj: SQLModel):
        return False