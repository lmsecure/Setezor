
from sqlmodel import Field, Relationship
from typing import List, Optional
from .import Base, IDDependent

class DNS_A(IDDependent, Base, table=True):
    __tablename__ = "network_dns_a"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения DNS A записей домена"
    }
    target_ip_id: str          = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP адреса"})
    target_domain_id: str      = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    

    target_ip: Optional["IP"]           = Relationship(back_populates="dns_a_target") # type: ignore
    target_domain: Optional["Domain"]   = Relationship(back_populates="dns_a_target") # type: ignore
    softwares: List["L4Software"] = Relationship(back_populates="dns_a") # type: ignore