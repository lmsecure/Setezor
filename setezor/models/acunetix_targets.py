
from setezor.models import IDDependent, Base
from sqlmodel import Field, Relationship



class AcunetixTargets(IDDependent, Base, table=True):

    __tablename__ = "acunetix_target"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения таргетов окуня"
    }
    acunetix_id: str = Field(foreign_key="acunetix.id", sa_column_kwargs={"comment": "Идентификатор окуня"})
    acunetix_target_id: str = Field(index=True, sa_column_kwargs={"comment": "ID инстанса в acunetix"})
    target_id: str = Field(index=True, sa_column_kwargs={"comment": "ID таргета в базе"})