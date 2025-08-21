from sqlmodel import SQLModel

from setezor.models import Employee
from setezor.repositories import SQLAlchemyRepository


class EmployeeRepository(SQLAlchemyRepository[Employee]):
    model = Employee

    async def exists(self, emp_obj: SQLModel):
        return False