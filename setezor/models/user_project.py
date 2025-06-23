from typing import List

from sqlmodel import Field, Relationship
from setezor.models import IDDependent, TimeDependent


class UserProject(IDDependent, TimeDependent, table=True):
    __tablename__ = "user_project"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения связи пользователь-проект"
    }
    
    user_id: str = Field(foreign_key="user.id", sa_column_kwargs={"comment":"Идентификатор пользователя"})
    project_id: str = Field(foreign_key="project.id", sa_column_kwargs={"comment":"Идентификатор проекта"})
    role_id: str = Field(foreign_key="user_role.id", sa_column_kwargs={"comment":"Идентификатор роли"})

    user: List["User"] = Relationship(back_populates="projects") # type: ignore
    project: List["Project"] = Relationship(back_populates="users") # type: ignore