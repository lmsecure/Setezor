from sqlmodel import Field, Relationship
from typing import List
from .import TimeDependent, IDDependent

class Hardware_Type(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_hardware_type"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации о типе железки на объекте"
    }

    name: str = Field(sa_column_kwargs={"comment":"Наименование типа железки"})

    hardwares: List["Hardware"] = Relationship(back_populates="hardware_type") # type: ignore