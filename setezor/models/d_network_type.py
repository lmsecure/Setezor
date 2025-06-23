from sqlmodel import Field, Relationship
from typing import List
from .import TimeDependent, IDDependent

class Network_Type(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_network_type"
    __table_args__ = {
        "comment": "Справочник типов сетей"
    }
    name: str = Field(sa_column_kwargs={"comment":"Наименование типа сети"})

    networks: List["Network"] = Relationship(back_populates="network_type") # type: ignore