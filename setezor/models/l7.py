from typing import Optional, List

from sqlmodel import Field, Relationship
from .import Base, IDDependent

class L7(IDDependent, Base, table=True):
    __tablename__ = "l7"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения ресурсов уровня приложения"
    }

    port_id: Optional[str]     = Field(foreign_key="port.id", sa_column_kwargs={"comment":"Идентификатор порта"})
    domain_id: Optional[str]   = Field(foreign_key="domain.id", sa_column_kwargs={"comment":"Идентификатор домена"})
    
    
    port: Optional["Port"]        = Relationship(back_populates="l7")
    domain: Optional["Domain"]    = Relationship(back_populates="l7")
    softwares: List["L7Software"] = Relationship(back_populates="l7")
    cert: List["Cert"]        = Relationship(back_populates="l7")
    authentication_credentials: List["L7_Authentication_Credentials"] = Relationship(back_populates="l7")
    