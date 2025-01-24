
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship
from typing import List, Optional

class L7Software(IDDependent, Base, table=True):
    __tablename__ = "l7_software"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения ПО, которое крутится на ресурсе уровня приложения"
    }

    l7_id: str   = Field(foreign_key="l7.id", sa_column_kwargs={"comment": "Идентификатор веб-ресурса"})
    software_id: str       = Field(foreign_key="d_software.id", sa_column_kwargs={"comment": "Идентификатор ПО"})

    parent_l7_software_id: Optional[str] = Field(foreign_key="l7_software.id", sa_column_kwargs={"comment":"Идентификатор родительского софта на ресурсе"})

    
    l7: "L7"              = Relationship(back_populates="softwares")
    software: "Software"  = Relationship(back_populates="l7")
    vulnerabilities: List["L7SoftwareVulnerability"] = Relationship(back_populates="l7_software")

    parent_l7_software: Optional["L7Software"] = Relationship(back_populates="child_l7_softwares", sa_relationship_kwargs={"remote_side": "[L7Software.id]"})
    child_l7_softwares: List["L7Software"]     = Relationship(back_populates="parent_l7_software")
