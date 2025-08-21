from sqlmodel import SQLModel

from setezor.models import Employee_Phone
from setezor.repositories import SQLAlchemyRepository


class EmployeePhoneRepository(SQLAlchemyRepository[Employee_Phone]):
    model = Employee_Phone

    async def exists(self, emp_phone_obj: SQLModel):
        return False