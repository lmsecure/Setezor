from typing import Optional, List

from sqlmodel import Field, Relationship
from .import ProjectDependent, IDDependent, TimeDependent

class Scope(IDDependent, TimeDependent, ProjectDependent, table=True):
    __tablename__ = "project_scope"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения скопов"
    }

    name: str                   = Field(sa_column_kwargs={"comment":"Наименование скоупа"})
    description: Optional[str]  = Field(sa_column_kwargs={"comment":"Описание скоупа"})
