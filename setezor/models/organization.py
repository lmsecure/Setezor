from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent


class Organization(IDDependent, Base, table=True):
    __tablename__ = "organization"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения организаций"
    }

    name: str
    departments: List["Department"] = Relationship(back_populates="organization") # type: ignore