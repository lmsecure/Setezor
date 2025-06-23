from setezor.models import IDDependent, TimeDependent, ProjectDependent
from sqlmodel import Field


class Acunetix(IDDependent, TimeDependent, ProjectDependent, table=True):

    __tablename__ = "setezor_tools_acunetix"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения окуней"
    }

    name: str     = Field(sa_column_kwargs={"comment": "Наименование инстанса Acunetix"})
    url: str      = Field(sa_column_kwargs={"comment": "Адрес инстанса Acunetix"})
    token: str    = Field(sa_column_kwargs={"comment": "Токен доступа Acunetix"})
    offset: str   = Field(sa_column_kwargs={"comment": "Часовой пояс"})
