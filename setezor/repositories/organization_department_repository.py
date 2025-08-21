from sqlmodel import SQLModel

from setezor.models import Department
from setezor.repositories import SQLAlchemyRepository


class OrganizationDepartmentRepository(SQLAlchemyRepository[Department]):
    model = Department

    async def exists(self, org_department_obj: SQLModel):
        return False