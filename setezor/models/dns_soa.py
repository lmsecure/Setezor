
from sqlmodel import Field, Relationship
from typing import Optional
from .import Base, IDDependent

class DNS_SOA(IDDependent, Base, table=True):
    __tablename__ = "network_dns_soa"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения DNS SOA записей домена"
    }
    target_ip_id: str          = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP адреса"})
    target_domain_id: str      = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    domain_nname_id: str = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    domain_rname_id: str = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})

    serial: str = Field(sa_column_kwargs={"comment":"Серийный номер"})
    refresh: int = Field(sa_column_kwargs={"comment":"Обновление"})
    retry: int = Field(sa_column_kwargs={"comment":"Попытка"})
    expire: int = Field(sa_column_kwargs={"comment":"Истекает"})
    ttl: int = Field(sa_column_kwargs={"comment":"TTL"})

    target_ip: Optional["IP"]           = Relationship(back_populates="dns_soa_target") # type: ignore
    target_domain: Optional["Domain"]   = Relationship(back_populates="dns_soa_target", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.target_domain_id]"}) # type: ignore
    domain_nname: Optional["Domain"]   = Relationship(back_populates="dns_soa_domain_nname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_nname_id]"}) # type: ignore
    domain_rname: Optional["Domain"]   = Relationship(back_populates="dns_soa_domain_rname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_rname_id]"}) # type: ignore