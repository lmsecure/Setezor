
from setezor.models import TimeDependent, IDDependent
from sqlmodel import Field, Relationship
from typing import Optional, List

class SoftwareType(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_software_type"
    __table_args__ = {
        "comment": "Таблица предназначена для типа софта"
    }
    name: Optional[str] = Field(sa_column_kwargs={"comment": "Наименование типа софта"})
    softwares: List["Software"] = Relationship(back_populates="_type") # type: ignore
    