
from sqlmodel import Field, Relationship
from .import Base, IDDependent
from typing import List, Optional

class Port(IDDependent, Base, table=True):
    __tablename__ = "network_port"
    __table_args__ = {
        "comment": "Таблица предназначена для портов на конкретном IP"
    }

    port: int           = Field(index=True, sa_column_kwargs={"comment":"Номер порта"})
    ip_id: str      = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP"})
    protocol: str       = Field(default="", sa_column_kwargs={"comment":"Протокол порта"})
    service_name: Optional[str]   = Field(default="", sa_column_kwargs={"comment":"Наименование сервиса порта"})
    state: str          = Field(default="", sa_column_kwargs={"comment":"Состояние порта"})
    ttl: Optional[int]  = Field(sa_column_kwargs={"comment":"TTL из nmap"})
    is_ssl: Optional[bool] = Field(sa_column_kwargs={"comment":"Есть ли SSL на порту"})


    ip: "IP"         = Relationship(back_populates="ports") # type: ignore
    softwares: List["L4Software"] = Relationship(back_populates="l4") # type: ignore
    authentication_credentials: List["Authentication_Credentials"] = Relationship(back_populates="port") # type: ignore