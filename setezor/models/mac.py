from typing import Optional, List

from pydantic import field_serializer
from sqlmodel import Field, Relationship
from .import Base, IDDependent
from pydantic_extra_types.mac_address import MacAddress

class MAC(IDDependent, Base, table=True):
    __tablename__ = "network_mac"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения MAC адресов"
    }

    mac: Optional[str]   = Field(default='', index=True, sa_column_kwargs={"comment":"MAC адрес"})
    object_id: str   = Field(foreign_key="object.id", sa_column_kwargs={"comment":"Идентификатор объекта"})
    name: Optional[str]  = Field(default='', sa_column_kwargs={"comment": "Наименование интерфейса"})
    vendor_id: Optional[str]   = Field(foreign_key="setezor_d_vendor.id", sa_column_kwargs={"comment":"Идентификатор вендора"})

    ips: List["IP"]              = Relationship(back_populates="mac") # type: ignore
    object: Optional["Object"]   = Relationship(back_populates="macs") # type: ignore
    vendor: "Vendor" = Relationship(back_populates="macs") # type: ignore

    @field_serializer('mac')
    def serialize_mac(self, mac: int | None, _info):
        if not mac: return None
        return str(MacAddress(mac))
