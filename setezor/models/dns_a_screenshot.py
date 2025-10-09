from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship


class DNS_A_Screenshot(IDDependent, Base, table=True):
    __tablename__ = "network_dns_a_screenshot"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения связи между DNS записью и скриншотом"
    }

    dns_id: str = Field(
        foreign_key="network_dns.id", sa_column_kwargs={"comment": "Идентификатор DNS записи"}
    )
    screenshot_id: str = Field(
        foreign_key="screenshot.id", sa_column_kwargs={"comment": "Идентификатор скриншота"}
    )

    dns: "DNS" = Relationship(back_populates="screenshots")  # type: ignore
    screenshot: "Screenshot" = Relationship(back_populates="dns_records")  # type: ignore
