from sqlmodel import Field, Relationship
from setezor.models import TimeDependent, IDDependent
from typing import List, Optional

class Vendor(IDDependent, TimeDependent, table=True):
    __tablename__ = "d_vendor"
    __table_args__ = {
        "comment": "Справочник вендоров"
    }

    name: Optional[str] = Field(sa_column_kwargs={"comment":"Наименование вендора"})

    softwares: List["Software"] = Relationship(back_populates="vendor")
    hardwares: List["Hardware"] = Relationship(back_populates="vendor")
    macs: List["MAC"]           = Relationship(back_populates="vendor")