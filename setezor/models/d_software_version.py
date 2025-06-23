
from setezor.models import TimeDependent, IDDependent
from sqlmodel import Field, Relationship
from typing import Optional, List

class SoftwareVersion(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_d_software_version"
    __table_args__ = {
        "comment": "Таблица предназначена для типа софта"
    }
    version: Optional[str] = Field(index=True, sa_column_kwargs={"comment": "Версия софта"})
    build: Optional[str] = Field(index=True, sa_column_kwargs={"comment": "Билд софта"})
    cpe23: Optional[str] = Field(index=True, sa_column_kwargs={"comment": "CPE23 строка софта"})
    software_id: Optional[str] = Field(foreign_key="setezor_d_software.id", sa_column_kwargs={"comment": "Идентификатор софта"})

    software: "Software" = Relationship(back_populates="versions") # type: ignore
    port_softwares: List["L4Software"] = Relationship(back_populates="software_version") # type: ignore