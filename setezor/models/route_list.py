
from sqlmodel import Field, Relationship
from .import Base, IDDependent

class RouteList(IDDependent, Base, table=True):
    __tablename__ = "network_route_list"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения позиции IP адреса в определённом роуте"
    }

    ip_id_from: str      = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP"})
    ip_id_to: str      = Field(foreign_key="network_ip.id", sa_column_kwargs={"comment":"Идентификатор IP"})
    route_id: str   = Field(foreign_key="network_route.id", sa_column_kwargs={"comment":"Идентификатор Route"})

    
    ip_from: "IP"         = Relationship(back_populates="route_lists_from", sa_relationship_kwargs={"foreign_keys": "[RouteList.ip_id_from]"}) # type: ignore
    ip_to: "IP"         = Relationship(back_populates="route_lists_to", sa_relationship_kwargs={"foreign_keys": "[RouteList.ip_id_to]"}) # type: ignore
    route: "Route"   = Relationship(back_populates="route_lists") # type: ignore


    def __repr__(self):
        return f"RouteList(deleted_at={self.deleted_at}, created_by={self.created_by}, id={self.id}, ip_from={repr(self.ip_from)}, ip_to={repr(self.ip_from)}, route={repr(self.route)})"