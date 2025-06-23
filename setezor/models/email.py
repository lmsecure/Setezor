from sqlmodel import Field, Relationship
from typing import List
from .import Base, IDDependent

class Email(IDDependent, Base, table=True):
    __tablename__ = "organization_email"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения отношений почта-сотрудник"
    }
    
    email: str = Field(sa_column_kwargs={"comment":"Адрес электронной почты"})

    employees: List["Employee_Email"] = Relationship(back_populates="email") # type: ignore