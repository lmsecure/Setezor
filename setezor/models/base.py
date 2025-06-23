import uuid
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

def generate_unique_id() -> str:
    return uuid.uuid4().hex

class TimeDependent(SQLModel):
    created_at: datetime             = Field(sa_column_kwargs={"default":datetime.now,"comment":"Дата-время создания сущности"})
    updated_at: Optional[datetime]   = Field(sa_column_kwargs={"onupdate": datetime.now,"comment":"Дата-время изменения сущности"},)
    deleted_at: Optional[datetime]   = Field(default=None, nullable=True, sa_column_kwargs={"comment":"Дата-время удаления сущности"},)


class IDDependent(SQLModel):
    id: Optional[str] = Field(sa_column_kwargs={"default": generate_unique_id}, primary_key=True)

class ProjectDependent(SQLModel):
    project_id: Optional[str]   = Field(foreign_key="project.id", sa_column_kwargs={"comment":"Идентификатор проекта"})
    created_by: Optional[str]   = Field(default="", sa_column_kwargs={"comment":"Задача, породившая сущность"})

class Base(TimeDependent, ProjectDependent):
    scan_id: Optional[str]      = Field(foreign_key="project_scan.id", sa_column_kwargs={"comment":"Идентификатор скана"})
