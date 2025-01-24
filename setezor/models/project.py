
from sqlmodel import Field, Relationship
from setezor.models import IDDependent, TimeDependent
from typing import List, Optional

class Project(IDDependent, TimeDependent, table=True):
    __tablename__ = "project"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения проектов"
    }


    name: str     = Field(sa_column_kwargs={"comment":"Название проекта"})
    description: Optional[str]   = Field(sa_column_kwargs={"comment":"Описание проекта"})
    search_vulns_token: Optional[str] = Field(sa_column_kwargs={"comment":"Токен для search vulns"})


    users: List["UserProject"] = Relationship(back_populates="project")