from typing import Optional, List
from sqlmodel import Field, Relationship
from .import Base, IDDependent

class Route(IDDependent, Base, table=True):
    __tablename__ = "network_route"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения роутов"
    }

    agent_id: str = Field(foreign_key="setezor_agent_in_project.id")


    route_lists: List["RouteList"] = Relationship(back_populates="route") # type: ignore

