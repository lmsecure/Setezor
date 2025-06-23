from typing import List, Optional

from sqlmodel import Field, Relationship
from .import TimeDependent, IDDependent

class Agent(IDDependent, TimeDependent, table=True):
    __tablename__ = "setezor_agent"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации об агенте"
    }

    name: str                    = Field(default="Smith", sa_column_kwargs={"comment":"Имя агента"})
    description: str             = Field(sa_column_kwargs={"comment":"Описание агента"})
    rest_url: str                = Field(sa_column_kwargs={"comment":"Адрес на котором запущен агент"})
    secret_key: Optional[str]    = Field(default="", sa_column_kwargs={"comment": "AES256 ключ агента"})
    user_id: Optional[str]       = Field(foreign_key="user.id", sa_column_kwargs={"comment": "Идентификатор владельца"})
    is_connected: bool           = Field(default=False, sa_column_kwargs={"comment": "Подключен ли агент"})
    flag: Optional[bool]                   = Field(default=False, sa_column_kwargs={"comment": "Флаг агента"})

    user: "User" = Relationship(back_populates="agents") # type: ignore
    projects: List["AgentInProject"] = Relationship(back_populates="agent") # type: ignore