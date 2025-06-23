
from setezor.models import Base, IDDependent
from sqlmodel import Field


class Screenshot(IDDependent, Base, table=True):
    __tablename__ = "software_web_screenshot"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения скриншотов на веб-ресурсе"
    }

    path: str             = Field(sa_column_kwargs={"comment": "Путь до скриншота"})
    resource_id: str   = Field(sa_column_kwargs={"comment": "Идентификатор ресурса"})