
from sqlmodel import Field, Relationship
from typing import Optional
from .import Base, IDDependent

class L7_Authentication_Credentials(IDDependent, Base, table=True):
    __tablename__ = "authentication_credentials"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения данных авторизации на ресурс"
    }

    l7_id: str = Field(foreign_key="l7.id",sa_column_kwargs={"comment":"Идентификатор ресурса"})
    login: str = Field(sa_column_kwargs={"comment":"Логин"})
    password: Optional[str] = Field(sa_column_kwargs={"comment":"Пароль"})
    need_auth: bool = Field(sa_column_kwargs={"comment":"Нужна ли авторизация"})
    role: Optional[str] = Field(sa_column_kwargs={"comment":"Роль"})
    permissions: int = Field(sa_column_kwargs={"comment":"Права"})
    parameters: Optional[str] = Field(sa_column_kwargs={"comment":"Параметры"})
    
    
    l7: "L7" = Relationship(back_populates="authentication_credentials")