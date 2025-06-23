from sqlmodel import Relationship, Field
from typing import List, Optional
from .import Base, IDDependent

class Domain(IDDependent, Base, table=True):
    __tablename__ = "network_domain"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения доменных имён"
    }

    domain: Optional[str] = Field(default="", index=True, sa_column_kwargs={"comment":"Доменное имя"})
    

    dns_a_target: List["DNS_A"]             = Relationship(back_populates="target_domain") # type: ignore
    
    dns_mx_target: List["DNS_MX"]           = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.target_domain_id]"}) # type: ignore
    dns_mx_value: List["DNS_MX"]            = Relationship(back_populates="value_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.value_domain_id]"}) # type: ignore
    
    dns_cname_target: List["DNS_CNAME"]     = Relationship(back_populates="target_domain") # type: ignore
    
    dns_ns_target: List["DNS_NS"]           = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_NS.target_domain_id]"}) # type: ignore
    dns_ns_value: List["DNS_NS"]            = Relationship(back_populates="value_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_NS.value_domain_id]"}) # type: ignore
    
    dns_txt_target: List["DNS_TXT"]         = Relationship(back_populates="target_domain") # type: ignore
    
    dns_soa_target: List["DNS_SOA"]         = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.target_domain_id]"}) # type: ignore
    dns_soa_domain_nname: List["DNS_SOA"]   = Relationship(back_populates="domain_nname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_nname_id]"}) # type: ignore
    dns_soa_domain_rname: List["DNS_SOA"]   = Relationship(back_populates="domain_rname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_rname_id]"}) # type: ignore

    whois: List["WhoIsDomain"]   = Relationship(back_populates="domain") # type: ignore
    project: "Project" = Relationship(back_populates="domains") # type: ignore