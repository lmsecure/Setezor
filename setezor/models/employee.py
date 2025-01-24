
from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent


class Employee(IDDependent, Base, table=True):
    __tablename__ = "employee"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения сотрудников"
    }

    first_name: str = Field(sa_column_kwargs={"comment":"Имя"})
    middle_name: str = Field(sa_column_kwargs={"comment":"Отчество"})
    last_name: str = Field(sa_column_kwargs={"comment":"Фамилия"})
    position: str = Field(sa_column_kwargs={"comment":"Должность"})
    manager_id: Optional[str] = Field(foreign_key="employee.id", sa_column_kwargs={"comment":"Идентификатор вышестоящего сотрудника"})
    department_id: Optional[str] = Field(foreign_key="department.id", sa_column_kwargs={"comment":"Идентификатор департамента"})

    department: Optional["Department"] = Relationship(back_populates="employees")
    objects: List["Object_Employee"] = Relationship(back_populates="employee")
    phones: List["Employee_Phone"] = Relationship(back_populates="employee")
    emails: List["Employee_Email"] = Relationship(back_populates="employee")
    
    manager: Optional["Employee"] = Relationship(back_populates="subordinates", sa_relationship_kwargs={"remote_side": "[Employee.id]"})
    subordinates: List["Employee"] = Relationship(back_populates="manager")