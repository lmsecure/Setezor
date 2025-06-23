from typing import List, Optional

from sqlmodel import Field, Relationship

from setezor.models.d_object_type import ObjectType
from setezor.models.mac import MAC
from setezor.models.object_employee import Object_Employee
from .import Base, IDDependent

class Object(IDDependent, Base, table=True):
    __tablename__ = "object"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения объектов"
    }

    object_type_id: Optional[str] = Field(default=str("3d9cf6c43fd54aacb88878f5425f43c4"), foreign_key="setezor_d_object_type.id", sa_column_kwargs={"comment":"Идентификатор типа объекта"})
    critical_level: int = Field(default=0, sa_column_kwargs={"comment":"Уровень критичности объекта"})
    note: Optional[str] = Field(sa_column_kwargs={"comment":"Примечание к объекту"})
    agent_id: Optional[str] = Field(sa_column_kwargs={"comment":"Идентификатор агента"})

    macs: List["MAC"] = Relationship(back_populates="object")
    object_type: Optional["ObjectType"] = Relationship(back_populates="objects")
    employees: List["Object_Employee"]  = Relationship(back_populates="object")
    agents: List["AgentInProject"] = Relationship(back_populates="_object") # type: ignore
    project: "Project" = Relationship(back_populates="objects") # type: ignore