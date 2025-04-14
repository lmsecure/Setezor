from sqlmodel import Relationship, Field
from typing import List, Optional
from .import Base, IDDependent

class Domain(IDDependent, Base, table=True):
    __tablename__ = "domain"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения доменных имён"
    }

    domain: Optional[str] = Field(default="", index=True, sa_column_kwargs={"comment":"Доменное имя"})
    

    dns_a_target: List["DNS_A"]             = Relationship(back_populates="target_domain")
    
    dns_mx_target: List["DNS_MX"]           = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.target_domain_id]"})
    dns_mx_value: List["DNS_MX"]            = Relationship(back_populates="value_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_MX.value_domain_id]"})
    
    dns_cname_target: List["DNS_CNAME"]     = Relationship(back_populates="target_domain")
    
    dns_ns_target: List["DNS_NS"]           = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_NS.target_domain_id]"})
    dns_ns_value: List["DNS_NS"]            = Relationship(back_populates="value_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_NS.value_domain_id]"})
    
    dns_txt_target: List["DNS_TXT"]         = Relationship(back_populates="target_domain")
    
    dns_soa_target: List["DNS_SOA"]         = Relationship(back_populates="target_domain", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.target_domain_id]"})
    dns_soa_domain_nname: List["DNS_SOA"]   = Relationship(back_populates="domain_nname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_nname_id]"})
    dns_soa_domain_rname: List["DNS_SOA"]   = Relationship(back_populates="domain_rname", sa_relationship_kwargs={"foreign_keys": "[DNS_SOA.domain_rname_id]"})

    whois: List["WhoIsDomain"]   = Relationship(back_populates="domain")
    project: "Project" = Relationship(back_populates="domains")