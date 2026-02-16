from sqlmodel import Field, Relationship

from setezor.models import Base, IDDependent


class WebArchive(IDDependent, Base, table=True):
    __tablename__ = "network_web_archive"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения web архивов"
    }
    name: str = Field(sa_column_kwargs={"comment": "Название архива"})
    url: str = Field(sa_column_kwargs={"comment": "Полная ссылка на таргет"})
    dns_id: str = Field(
        foreign_key="network_dns.id", sa_column_kwargs={"comment": "Идентификатор DNS записи"}
    )

    dns: "DNS" = Relationship(back_populates="web_archives")  # type: ignore