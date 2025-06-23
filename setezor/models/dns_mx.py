
from sqlmodel import Field, Relationship
from typing import Optional
from .import Base, IDDependent

class DNS_MX(IDDependent, Base, table=True):
    __tablename__ = "network_dns_mx"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения DNS MX записей домена"
    }
    target_ip_id: str       = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP адреса"})
    target_domain_id: str   = Field(foreign_key="network_domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    value_domain_id: str    = Field(foreign_key="network_domain.id",sa_column_kwargs={"comment":"Идентификатор домена"})
    priority: int               = Field(sa_column_kwargs={"comment":"Приоритет"})

    target_ip: Optional["IP"]           = Relationship(back_populates="dns_mx_target") # type: ignore
    target_domain: Optional["Domain"]   = Relationship(back_populates="dns_mx_target", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.target_domain_id]"}) # type: ignore
    value_domain: Optional["Domain"]    = Relationship(back_populates="dns_mx_value", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.value_domain_id]"}) # type: ignore