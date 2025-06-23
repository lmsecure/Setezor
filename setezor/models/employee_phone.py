
from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent


class Employee_Phone(IDDependent, Base, table=True):
    __tablename__ = "employee_phone"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отношений телефон-сотрудник"
    }

    employee_id: str = Field(foreign_key="employee.id", sa_column_kwargs={"comment":"Идентификатор сотрудника"})
    phone_id: str = Field(foreign_key="organization_phone.id", sa_column_kwargs={"comment":"Идентификатор телефона"})

    employee: "Employee" = Relationship(back_populates="phones") # type: ignore
    phone: "Phone" = Relationship(back_populates="employees") # type: ignore