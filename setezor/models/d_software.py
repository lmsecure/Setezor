
from setezor.models import TimeDependent, IDDependent
from sqlmodel import Field, Relationship
from typing import Optional, List

class Software(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_software"
    __table_args__ = {
        "comment": "Таблица предназначена для ПО вендора"
    }
    
    vendor_id: str              = Field(foreign_key="setezor_d_vendor.id", sa_column_kwargs={"comment": "Идентификатор вендора"})
    type_id: Optional[str]      = Field(foreign_key="setezor_d_software_type.id", sa_column_kwargs={"comment": "Идентификатор типа софта"})
    product: Optional[str]      = Field(index=True, sa_column_kwargs={"comment": "Продукт вендора"})
    
    vendor: "Vendor"         = Relationship(back_populates="softwares") # type: ignore
    _type: "SoftwareType"    = Relationship(back_populates="softwares") # type: ignore
    versions: List["SoftwareVersion"] = Relationship(back_populates="software") # type: ignore
