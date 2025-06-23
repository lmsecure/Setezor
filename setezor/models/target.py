from typing import Optional, List

from sqlmodel import Field, Relationship
from .import ProjectDependent, IDDependent, TimeDependent

class Target(IDDependent, TimeDependent, ProjectDependent, table=True):
    __tablename__ = "project_scope_targets"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения таргетов скопа"
    }

    protocol: Optional[str]  = Field(sa_column_kwargs={"comment":"Схема таргета"})
    ip: Optional[str]      = Field(sa_column_kwargs={"comment":"IP таргета"})
    domain: Optional[str]  = Field(sa_column_kwargs={"comment":"Domain таргета"})
    port: Optional[int]    = Field(sa_column_kwargs={"comment":"Port таргета"})
    scope_id: str      = Field(foreign_key="project_scope.id", sa_column_kwargs={"comment":"Идентификатор скопа"})
