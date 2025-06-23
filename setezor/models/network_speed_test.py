from sqlmodel import Field, Relationship
from .import Base, IDDependent


class NetworkSpeedTest(IDDependent, Base, table=True):
    __tablename__ = "network_speed_test"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения замеренной пропускной способности между машинами (агентами)"
    }

    ip_id_from: str =   Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор интерфейса с которого отправлялись пакеты"})
    ip_id_to: str =     Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор интерфейса на который отправлялись пакеты"})
    speed: float =      Field(sa_column={"comment":"Замеренная скорость [mbps]"})
    port: int =         Field(sa_column_kwargs={"comment":"Номер порта на котором происходил замер"}, index=True)
    protocol: str =     Field(sa_column_kwargs={"comment":"Протокол на котором происходил замер"}, index=True)

    ip_from: "IP" = Relationship(back_populates="network_speed_test_from", sa_relationship_kwargs={"foreign_keys": "[NetworkSpeedTest.ip_id_from]"}) # type: ignore
    ip_to: "IP" = Relationship(back_populates="network_speed_test_to", sa_relationship_kwargs={"foreign_keys": "[NetworkSpeedTest.ip_id_to]"}) # type: ignore
