
from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent


class Employee_Email(IDDependent, Base, table=True):
    __tablename__ = "employee_email"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отношений почта-сотрудник"
    }

    employee_id: str = Field(foreign_key="employee.id", sa_column_kwargs={"comment":"Идентификатор сотрудника"})
    email_id: str = Field(foreign_key="organization_email.id", sa_column_kwargs={"comment":"Идентификатор почты"})

    employee: "Employee" = Relationship(back_populates="emails") # type: ignore
    email: "Email" = Relationship(back_populates="employees") # type: ignore