from sqlmodel import Field, Relationship
from setezor.models import IDDependent, TimeDependent
from typing import List


class User(IDDependent, TimeDependent, table=True):
    __tablename__ = "user"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения пользователей"
    }
    
    login: str = Field(sa_column_kwargs={"comment": "Логин пользователя"})
    hashed_password: str = Field(sa_column_kwargs={"comment": "Хеш пароля"})
    is_superuser: bool = Field(default=False, sa_column_kwargs={"comment": "Является ли суперпользователем"})

    projects: List["UserProject"] = Relationship(back_populates="user") # type: ignore
    agents: List["Agent"] = Relationship(back_populates="user") # type: ignore