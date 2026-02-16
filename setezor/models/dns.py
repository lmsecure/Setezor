from sqlmodel import Field, Relationship
from typing import List, Optional
from .import Base, IDDependent


class DNS(IDDependent, Base, table=True):
    __tablename__ = "network_dns"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения DNS записей домена"
    }
    dns_type_id: Optional[str]     = Field(foreign_key="setezor_d_dns_type.id", sa_column_kwargs={"comment":"Идентификатор типа DNS"})
    target_ip_id: Optional[str]    = Field(foreign_key="network_ip.id",         sa_column_kwargs={"comment":"Идентификатор IP адреса"})
    target_domain_id: str          = Field(foreign_key="network_domain.id",     sa_column_kwargs={"comment":"Идентификатор домена"})
    value_domain_id: Optional[str] = Field(foreign_key="network_domain.id",     sa_column_kwargs={"comment":"Идентификатор полученного домена"})

    ttl: Optional[int]             = Field(sa_column_kwargs={"comment":"TTL"})
    extra_data: Optional[str]      = Field(sa_column_kwargs={"comment":"Дополнительные данные в формате json"})

    dns_type: "DNS_Type"                  = Relationship(back_populates="dns_objs")   # type: ignore
    target_ip: Optional["IP"]             = Relationship(back_populates="dns_target") # type: ignore
    target_domain: "Domain"               = Relationship(back_populates="dns_target", sa_relationship_kwargs={"foreign_keys": "[DNS.target_domain_id]"}) # type: ignore
    value_domain: Optional["Domain"]      = Relationship(back_populates="dns_value",  sa_relationship_kwargs={"foreign_keys": "[DNS.value_domain_id]"})  # type: ignore
    softwares: List["L4Software"]         = Relationship(back_populates="dns")        # type: ignore
    screenshots: List["DNS_A_Screenshot"] = Relationship(back_populates="dns")        # type: ignore
    web_archives: List["WebArchive"]      = Relationship(back_populates="dns")        # type: ignore
