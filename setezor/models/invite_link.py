from sqlmodel import Field
from setezor.models import IDDependent, TimeDependent
from typing import List


class Invite_Link(IDDependent, TimeDependent, table=True):
    __tablename__ = "user_invite_link"
    __table_args__ = {
        "comment": "Таблица предназначена для ролей пользователя в проектах"
    }
    
    token_hash: str = Field(index=True, sa_column_kwargs={"comment": "Хеш от токена"})
    token: str = Field(sa_column_kwargs={"comment": "Токен с пэйлодом"})
    count_of_entries: int = Field(nullable=True, sa_column_kwargs={"comment": "Количество допустимых использований"})