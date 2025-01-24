from typing import List, Optional

from sqlmodel import Field, Relationship
from .import Base, IDDependent

class Agent(IDDependent, Base, table=True):
    __tablename__ = "agent"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации об агенте"
    }

    name: str                            = Field(default="Smith", sa_column_kwargs={"comment":"Имя агента"})
    description: str                     = Field(sa_column_kwargs={"comment":"Описание агента"})
    color: str                           = Field(sa_column_kwargs={"comment":"Цвет агента на карте"})
    rest_url: str                        = Field(sa_column_kwargs={"comment":"Адрес на котором запущен агент"})
    parent_agent_id: Optional[str]   = Field(sa_column_kwargs={"comment":"Идентификатор агентского инстанса"})
    object_id: str                   = Field(foreign_key="object.id", sa_column_kwargs={"comment":"Идентификатор Object'a, который является агентом"})
    secret_key: Optional[str]            = Field(sa_column_kwargs={"comment": "AES256 ключ агента"})

    route: List["Route"]   = Relationship(back_populates="agent")
