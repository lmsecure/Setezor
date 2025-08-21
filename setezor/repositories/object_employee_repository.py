from sqlmodel import SQLModel

from setezor.models import Object_Employee
from setezor.repositories import SQLAlchemyRepository


class ObjectEmployeeRepository(SQLAlchemyRepository[Object_Employee]):
    model = Object_Employee

    async def exists(self, emp_obj: SQLModel):
        return False