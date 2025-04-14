from typing import List, Optional

from sqlmodel import Field
from .import TimeDependent, IDDependent

class AgentParentAgent(IDDependent, TimeDependent, table=True):
    __tablename__ = "agent_parent_agent"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения агента и его родителей"
    }

    agent_id: str          = Field(foreign_key="agent.id", sa_column_kwargs={"comment": "Идентификатор агента"})
    parent_agent_id: str   = Field(foreign_key="agent.id", sa_column_kwargs={"comment":"Идентификатор родительского агента"})