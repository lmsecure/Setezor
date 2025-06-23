
from setezor.models import IDDependent, TimeDependent
from sqlmodel import Field

class AuthLog(IDDependent, TimeDependent, table=True):
    __tablename__ = "user_auth_log"
    __table_args__ = {
        "comment": "Таблица предназначена для логирования событий, связанных с авторизацией"
    }

    login: str = Field(sa_column_kwargs={"comment":"Имя пользователя"})
    event: str = Field(sa_column_kwargs={"comment": "Событие"})