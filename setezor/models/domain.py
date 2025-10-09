from sqlmodel import Relationship, Field
from typing import List, Optional
from .import Base, IDDependent

class Domain(IDDependent, Base, table=True):
    __tablename__ = "network_domain"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения доменных имён"
    }

    domain: Optional[str] = Field(default="", index=True, nullable=False, sa_column_kwargs={"comment":"Доменное имя"})

    dns_target: List["DNS"]      = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS.target_domain_id]"}) # type: ignore
    dns_value: List["DNS"]       = Relationship(back_populates="value_domain",  sa_relationship_kwargs={"foreign_keys": "[DNS.value_domain_id]"}) # type: ignore

    whois: List["WhoIsDomain"]   = Relationship(back_populates="domain") # type: ignore
    project: "Project" = Relationship(back_populates="domains") # type: ignore