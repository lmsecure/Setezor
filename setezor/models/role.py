from sqlmodel import Field, Relationship
from setezor.models import IDDependent, TimeDependent
from typing import List


class Role(IDDependent, TimeDependent, table=True):
    __tablename__ = "user_role"
    __table_args__ = {
        "comment": "Таблица предназначена для ролей пользователя в проектах"
    }
    
    name: str = Field(sa_column_kwargs={"comment": "Название роли"})