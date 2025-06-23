
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship
from typing import List, Optional

class L4Software(IDDependent, Base, table=True):
    __tablename__ = "network_port_software"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения ПО, которое крутится на ресурсе уровня 4"
    }

    l4_id: str   = Field(foreign_key="network_port.id", sa_column_kwargs={"comment": "Идентификатор порта"})
    software_version_id: Optional[str]  = Field(foreign_key="setezor_d_software_version.id", sa_column_kwargs={"comment": "Идентификатор ПО"})
    dns_a_id: Optional[str] = Field(foreign_key="network_dns_a.id", sa_column_kwargs={"comment": "Идентификатор DNS записи"})

    l4: "Port"              = Relationship(back_populates="softwares") # type: ignore
    software_version: "SoftwareVersion"  = Relationship(back_populates="port_softwares") # type: ignore
    dns_a: "DNS_A" = Relationship(back_populates="softwares") # type: ignore
    vulnerabilities: List["L4SoftwareVulnerability"] = Relationship(back_populates="l4_software") # type: ignore
