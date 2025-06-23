from .base import IDDependent, TimeDependent
from sqlmodel import Field, Relationship
from typing import Optional, List


class ObjectType(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_object_type"
    __table_args__ = {
        "comment": "Справочник типов объектов"
    }

    name: Optional[str] = Field(sa_column_kwargs={"comment": "Наименование типа устройства"})

    objects: List["Object"] = Relationship(back_populates="object_type") # type: ignore