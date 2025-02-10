from sqlmodel import Field
from setezor.models import IDDependent, TimeDependent
from typing import List


class Invite_Link(IDDependent, TimeDependent, table=True):
    __tablename__ = "invite_link"
    __table_args__ = {
        "comment": "Таблица предназначена для ролей пользователя в проектах"
    }
    
    token_hash: str = Field(index=True, sa_column_kwargs={"comment": "Хеш от токена"})
    token: str = Field(sa_column_kwargs={"comment": "Токен с пэйлодом"})
    used: bool = Field(default=False)