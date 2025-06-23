from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent

class Phone(IDDependent, Base, table=True):
    __tablename__ = "organization_phone"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отношений телефон-сотрудник"
    }

    phone: str = Field(sa_column_kwargs={"comment":"Номер телефона"})

    employees: List["Employee_Phone"] = Relationship(back_populates="phone") # type: ignore