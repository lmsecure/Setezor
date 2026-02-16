
from sqlmodel import Field
from typing import Optional
from .import Base, IDDependent

class Task(IDDependent, Base, table=True):
    __tablename__ = "project_task"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения запускаемых задач"
    }

    status: str = Field(sa_column_kwargs={"comment":"Статус задачи"})
    params: str = Field(sa_column_kwargs={"comment":"Аргументы задачи"})
    user_id: str = Field(foreign_key="user.id", sa_column_kwargs={"comment": "Идентификатор пользователя"})
    agent_id: Optional[str] = Field(foreign_key="setezor_agent.id", sa_column_kwargs={"comment":"Идентификатор агента"})
    traceback: Optional[str] = Field(sa_column_kwargs={"comment": "Описание ошибки"})