from .base import IDDependent, TimeDependent
from sqlmodel import Field, Relationship
from typing import Optional, List


class DNS_Type(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_dns_type"
    __table_args__ = {
        "comment": "Справочник типов DNS записей"
    }

    name: Optional[str] = Field(sa_column_kwargs={"comment": "Наименование типа DNS"})

    dns_objs: List["DNS"] = Relationship(back_populates="dns_type") # type: ignore