from sqlmodel import SQLModel

from setezor.models import Employee_Email
from setezor.repositories import SQLAlchemyRepository


class EmployeeEmailRepository(SQLAlchemyRepository[Employee_Email]):
    model = Employee_Email

    async def exists(self, emp_email_obj: SQLModel):
        return False