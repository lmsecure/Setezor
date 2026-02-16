from sqlmodel import Field, Relationship
from . import TimeDependent, ProjectDependent, IDDependent


class AgentInterface(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_agent_network_interface"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения интерфейсов агента"
    }
    agent_id: str    = Field(foreign_key="setezor_agent.id", sa_column_kwargs={"comment": "Идентификатор агента"})
    ip: str          = Field(sa_column_kwargs={"comment": "IP интерфейса"})
    mac: str         = Field(sa_column_kwargs={"comment": "MAC интерфейса"})
    name: str        = Field(sa_column_kwargs={"comment": "Название интерфейса"})
    is_default: bool = Field(default=False)

    agent: "Agent"   = Relationship(back_populates="interfaces", sa_relationship_kwargs={"lazy": "selectin"})  # type: ignore
