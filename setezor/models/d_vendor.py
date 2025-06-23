from sqlmodel import Field, Relationship
from setezor.models import TimeDependent, IDDependent
from typing import List, Optional

class Vendor(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_vendor"
    __table_args__ = {
        "comment": "Справочник вендоров"
    }

    name: Optional[str] = Field(default='', index=True, sa_column_kwargs={"comment":"Наименование вендора"})

    softwares: List["Software"] = Relationship(back_populates="vendor") # type: ignore
    hardwares: List["Hardware"] = Relationship(back_populates="vendor") # type: ignore
    macs: List["MAC"]           = Relationship(back_populates="vendor") # type: ignore