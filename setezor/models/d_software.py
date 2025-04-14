
from setezor.models import TimeDependent, IDDependent
from sqlmodel import Field, Relationship
from typing import Optional, List

class Software(IDDependent, TimeDependent, table=True):
    __tablename__ = "d_software"
    __table_args__ = {
        "comment": "Таблица предназначена для ПО вендора"
    }
    
    vendor_id: str          = Field(foreign_key="d_vendor.id", sa_column_kwargs={"comment": "Идентификатор вендора"})
    product: Optional[str]      = Field(sa_column_kwargs={"comment": "Продукт вендора"})
    type: Optional[str]         = Field(sa_column_kwargs={"comment": "Тип софта"})
    version: Optional[str]      = Field(sa_column_kwargs={"comment": "Версия софта"})
    build: Optional[str]        = Field(sa_column_kwargs={"comment": "Билд софта"})
    patch: Optional[str]        = Field(sa_column_kwargs={"comment": "Патч софта"})
    platform: Optional[str]     = Field(sa_column_kwargs={"comment": "Платформа софта"})
    cpe23: Optional[str]        = Field(sa_column_kwargs={"comment": "Строка CPE23"})

    vendor: "Vendor"         = Relationship(back_populates="softwares")
    l4: List["L4Software"]   = Relationship(back_populates="software")