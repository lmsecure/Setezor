
from typing import List
from setezor.models import Base, IDDependent
from sqlmodel import Field, Relationship

class Screenshot(IDDependent, Base, table=True):
    __tablename__ = "screenshot"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения скриншотов на веб-ресурсе"
    }
    path: str  = Field(sa_column_kwargs={"comment": "Путь до скриншота"})
    
    l4_software_vulnerabilities: List["L4SoftwareVulnerabilityScreenshot"] = Relationship(back_populates="screenshot") # type: ignore
    dns_a_records: List["DNS_A_Screenshot"] = Relationship(back_populates="screenshot") # type: ignore