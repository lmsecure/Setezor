from typing import Optional, List

from sqlmodel import Field, Relationship
from .import ProjectDependent, IDDependent, TimeDependent

class Scan(IDDependent, TimeDependent, ProjectDependent, table=True):
    __tablename__ = "project_scan"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения сканов"
    }

    name: str                   = Field(sa_column_kwargs={"comment":"Наименование скана"})
    description: Optional[str]  = Field(sa_column_kwargs={"comment":"Описание скана"})
