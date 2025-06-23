
from sqlmodel import Field, Relationship
from typing import Optional
from .import Base, IDDependent

class DNS_CNAME(IDDependent, Base, table=True):
    __tablename__ = "network_dns_cname"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения DNS CNAME записей домена"
    }
    record_value: str       = Field(sa_column_kwargs={"comment":"Значение DNS записи"})
    target_ip_id: str          = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP адреса"})
    target_domain_id: str      = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    

    target_ip: Optional["IP"]           = Relationship(back_populates="dns_cname_target") # type: ignore
    target_domain: Optional["Domain"]   = Relationship(back_populates="dns_cname_target") # type: ignore