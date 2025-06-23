
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship

class WhoIsDomain(IDDependent, Base, table=True):
    __tablename__ = "software_web_whois_domain"
    __table_args__ = {
        "comment": "Таблица предназначена для информации о регистраторе веб-ресурса по domain"
    }

    domain_crt: str       = Field(sa_column_kwargs={"comment": "Доменное имя из whois"})
    data: str             = Field(sa_column_kwargs={"comment": "Весь вывод результата"})
    org_name: str         = Field(sa_column_kwargs={"comment": "Наименование организации"})
    AS: str               = Field(sa_column_kwargs={"comment": "Автономная система"})
    range_ip: str         = Field(sa_column_kwargs={"comment": "Диапазон IP"})
    netmask: str          = Field(sa_column_kwargs={"comment": "Маска сети"})
    domain_id: str    = Field(foreign_key="network_domain.id",sa_column_kwargs={"comment": "Идентификатор domain"})

    domain: "Domain" = Relationship(back_populates="whois") # type: ignore