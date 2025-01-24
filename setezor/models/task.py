
from sqlmodel import Field
from typing import Optional
from .import Base, IDDependent

class Task(IDDependent, Base, table=True):
    __tablename__ = "task"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения запускаемых задач"
    }

    status: str = Field(sa_column_kwargs={"comment":"Статус задачи"})
    params: str = Field(sa_column_kwargs={"comment":"Аргументы задачи"})
    agent_id: Optional[str] = Field(foreign_key="agent.id", sa_column_kwargs={"comment":"Идентификатор проекта"})