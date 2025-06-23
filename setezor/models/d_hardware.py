
from sqlmodel import Field, Relationship
from typing import Optional
from .import TimeDependent, IDDependent

class Hardware(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_hardware"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации о железке"
    }

    name: str = Field(sa_column_kwargs={"comment":"Наименование железки"})
    serial_number: Optional[str] = Field(sa_column_kwargs={"comment":"Серийный номер железки"})
    vendor_id: str = Field(foreign_key="setezor_d_vendor.id", sa_column_kwargs={"comment":"Идентификатор вендора"})
    hardware_type_id: str = Field(foreign_key="setezor_d_hardware_type.id", sa_column_kwargs={"comment":"Идентификатор типа железки"})

    hardware_type: "Hardware_Type" = Relationship(back_populates="hardwares") # type: ignore
    vendor: "Vendor" = Relationship(back_populates="hardwares") # type: ignore