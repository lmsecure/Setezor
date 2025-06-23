
from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent

class Network(IDDependent, Base, table=True):
    __tablename__ = "network"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения сетей"
    }

    start_ip: Optional[str]                        = Field(sa_column_kwargs={"comment":"Начальный IP адрес"})
    end_ip: Optional[str]                          = Field(sa_column_kwargs={"comment":"Конечный IP адрес"})
    mask: int                            = Field(default=24, sa_column_kwargs={"comment":"Маска сети"})
    gateway_id: Optional[str]                  = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор шлюза"})
    broadcast_id: Optional[str]                = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор широковещательного IP адреса"})
    network_type_id: str             = Field(default='b271a925283445c5ab60782a42466bfc', foreign_key="setezor_d_network_type.id", sa_column_kwargs={"comment":"Тип сети"})
    asn_id: str                      = Field(foreign_key="network_asn.id", sa_column_kwargs={"comment":"Идентификатор ASN"})
    parent_network_id: Optional[str] = Field(foreign_key="network.id", sa_column_kwargs={"comment":"Идентификатор родительской сети"})

    ips: List["IP"]                     = Relationship(back_populates="network", sa_relationship_kwargs={"foreign_keys": "[IP.network_id]"}) # type: ignore
    network_type: "Network_Type"        = Relationship(back_populates="networks") # type: ignore
    asn: "ASN"                          = Relationship(back_populates="networks") # type: ignore

    parent_network: Optional["Network"] = Relationship(back_populates="child_networks", sa_relationship_kwargs={"remote_side": "[Network.id]"})
    child_networks: List["Network"]     = Relationship(back_populates="parent_network")