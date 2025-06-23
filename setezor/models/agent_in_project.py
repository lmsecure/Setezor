from typing import List, Optional

from sqlmodel import Field, Relationship
from .import TimeDependent, ProjectDependent, IDDependent

class AgentInProject(IDDependent, TimeDependent, ProjectDependent, table=True):
    __tablename__ = "setezor_agent_in_project"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации об агенте"
    }

    color: str                       = Field(sa_column_kwargs={"comment":"Цвет агента на карте"})
    agent_id: str                    = Field(foreign_key="setezor_agent.id", sa_column_kwargs={"comment": "Идентификатор агента"})
    object_id: str                   = Field(foreign_key="object.id", sa_column_kwargs={"comment":"Идентификатор Object'a, который является агентом"})

    _object: "Object" = Relationship(back_populates="agents") # type: ignore
    agent: "Agent" = Relationship(back_populates="projects") # type: ignore
