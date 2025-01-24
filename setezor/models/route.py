from typing import Optional, List
from sqlmodel import Field, Relationship
from .import Base, IDDependent

class Route(IDDependent, Base, table=True):
    __tablename__ = "route"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения роутов"
    }

    agent_id: str = Field(foreign_key="agent.id")


    route_lists: List["RouteList"] = Relationship(back_populates="route")
    agent: "Agent" = Relationship(back_populates="route")


    def __repr__(self):
        return f"Route(deleted_at={self.deleted_at}, created_by={self.created_by}, id={self.id}, agent={repr(self.agent)}"
