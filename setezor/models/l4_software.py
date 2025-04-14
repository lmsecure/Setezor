
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship
from typing import List, Optional

class L4Software(IDDependent, Base, table=True):
    __tablename__ = "l4_software"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения ПО, которое крутится на ресурсе уровня 4"
    }

    l4_id: str   = Field(foreign_key="port.id", sa_column_kwargs={"comment": "Идентификатор порта"})
    software_id: str       = Field(foreign_key="d_software.id", sa_column_kwargs={"comment": "Идентификатор ПО"})
    dns_a_id: Optional[str] = Field(foreign_key="dns_a.id", sa_column_kwargs={"comment": "Идентификатор DNS записи"})

    l4: "Port"              = Relationship(back_populates="softwares")
    software: "Software"  = Relationship(back_populates="l4")
    dns_a: "DNS_A" = Relationship(back_populates="softwares")
    vulnerabilities: List["L4SoftwareVulnerability"] = Relationship(back_populates="l4_software")
