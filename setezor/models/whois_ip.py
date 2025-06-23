
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship



class WhoIsIP(IDDependent, Base, table=True):
    __tablename__ = "software_web_whois_ip"
    __table_args__ = {
        "comment": "Таблица предназначена для информации о регистраторе веб-ресурса по ip"
    }

    domain_crt: str   = Field(sa_column_kwargs={"comment": "Доменное имя из whois"})
    data: str         = Field(sa_column_kwargs={"comment": "Весь вывод результата"})
    org_name: str     = Field(sa_column_kwargs={"comment": "Наименование организации"})
    AS: str           = Field(sa_column_kwargs={"comment": "Автономная система"})
    range_ip: str     = Field(sa_column_kwargs={"comment": "Диапазон IP"})
    netmask: str      = Field(sa_column_kwargs={"comment": "Маска сети"})
    ip_id: str    = Field(foreign_key="network_ip.id",sa_column_kwargs={"comment": "Идентификатор ip"})

    ip: "IP" = Relationship(back_populates="whois") # type: ignore