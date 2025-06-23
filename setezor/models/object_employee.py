
from sqlmodel import Field, Relationship
from typing import Optional
from .import Base, IDDependent

class Object_Employee(IDDependent, Base, table=True):
    __tablename__ = "object_employee"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отношений сотрудник-арм"
    }
    object_id: str = Field(foreign_key="object.id", sa_column_kwargs={"comment":"Идентификатор объекта"})
    employee_id: str = Field(foreign_key="employee.id", sa_column_kwargs={"comment":"Идентификатор сотрудника"})

    object: "Object" = Relationship(back_populates="employees") # type: ignore
    employee: "Employee" = Relationship(back_populates="objects") # type: ignore