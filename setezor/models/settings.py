
from typing import Union
from setezor.models import Base, IDDependent
from sqlmodel import JSON, Column, Field


class Settings(IDDependent, table=True):
    __tablename__ = "setezor_settings"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения настроек"
    }

    name: str = Field(sa_column_kwargs={"comment": "Название параметра"})
    description: str = Field(sa_column_kwargs={"comment": "Описание параметра"})
    field: dict     = Field(sa_column=Column(JSON, comment="Значение параметра"))
    value_type: str = Field(sa_column_kwargs={"comment": "Тип параметра"})