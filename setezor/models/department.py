
from sqlmodel import Field, Relationship
from typing import List
from .import Base, IDDependent


class Department(IDDependent, Base, table=True):
    __tablename__ = "organization_department"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отделов в организации"
    }

    name: str = Field(sa_column_kwargs={"comment":"Наименование отдела"})
    organization_id: str = Field(foreign_key="organization.id", sa_column_kwargs={"comment":"Идентификатор организации"})

    organization: "Organization" = Relationship(back_populates="departments") # type: ignore
    employees: List["Employee"] = Relationship(back_populates="department") # type: ignore