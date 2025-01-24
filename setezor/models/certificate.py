
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship
from datetime import datetime

class Cert(IDDependent, Base, table=True):
    __tablename__ = "cert"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения информации о SSL сертификате"
    }

    data: str                   = Field(sa_column_kwargs={"comment":"Полный вывод информации о сертификате"})
    not_before_date: datetime   = Field(sa_column_kwargs={"comment":"Дата до"})
    not_after_date: datetime    = Field(sa_column_kwargs={"comment":"Дата после"})
    is_expired: bool            = Field(sa_column_kwargs={"comment":"Протухший ли сертификат"})
    alt_name: str               = Field(sa_column_kwargs={"comment":"Альтернативное имя"})
    l7_id: str            = Field(foreign_key="l7.id",sa_column_kwargs={"comment":"Идентификатор ресурса"})

    l7: "L7" = Relationship(back_populates="cert")