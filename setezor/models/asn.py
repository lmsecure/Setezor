
from sqlmodel import Field, Relationship
from typing import Optional, List
from .import Base, IDDependent

class ASN(IDDependent, Base, table=True):
    __tablename__ = "network_asn"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения ASN номеров"
    }
    
    number: Optional[int] = Field(sa_column_kwargs={"comment":"Номер ASN"})
    parent_asn_id: Optional[str] = Field(foreign_key="network_asn.id")
    
    
    networks: List["Network"] = Relationship(back_populates="asn") # type: ignore
    parent_asn: Optional["ASN"] = Relationship(back_populates="child_asns", sa_relationship_kwargs={"remote_side": "[ASN.id]"})
    child_asns: List["ASN"]     = Relationship(back_populates="parent_asn")
    project: "Project" = Relationship(back_populates="asns") # type: ignore