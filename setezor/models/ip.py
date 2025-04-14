from typing import Optional, List

from sqlmodel import Field, Relationship
from .import Base, IDDependent
from sqlalchemy import Column, ForeignKey

class IP(IDDependent, Base, table=True):
    __tablename__ = "ip"
    __table_args__ = {
        "comment": "Таблица предназначена для хранения IP адресов"
    }

    ip: Optional[str]             = Field(index=True, sa_column_kwargs={"comment":"IP адрес"})
    mac_id: Optional[str]     = Field(foreign_key="mac.id", sa_column_kwargs={"comment":"Идентификатор MAC адреса"})
    network_id: str           = Field(sa_column=Column(ForeignKey('network.id', use_alter=True), comment="Идентификатор сети"))

    mac: "MAC"                       = Relationship(back_populates="ips")
    ports: List["Port"]              = Relationship(back_populates="ip") 
    route_lists_from: List["RouteList"]   = Relationship(back_populates="ip_from", sa_relationship_kwargs={"foreign_keys": "[RouteList.ip_id_from]"})
    route_lists_to: List["RouteList"]   = Relationship(back_populates="ip_to", sa_relationship_kwargs={"foreign_keys": "[RouteList.ip_id_to]"})
    network: "Network"               = Relationship(back_populates="ips", sa_relationship_kwargs={"foreign_keys": "[IP.network_id]"})
    
    dns_a_target: List["DNS_A"]             = Relationship(back_populates="target_ip")
    
    dns_mx_target: List["DNS_MX"]           = Relationship(back_populates="target_ip")
    
    dns_cname_target: List["DNS_CNAME"]     = Relationship(back_populates="target_ip")
    
    dns_ns_target: List["DNS_NS"]           = Relationship(back_populates="target_ip")
    
    dns_txt_target: List["DNS_TXT"]         = Relationship(back_populates="target_ip")
    
    dns_soa_target: List["DNS_SOA"]         = Relationship(back_populates="target_ip")

    whois: List["WhoIsIP"]       = Relationship(back_populates="ip")
    cert: List["Cert"] = Relationship(back_populates="ip")

    #@field_serializer('ip', when_used='json')
    #def serialize_ip(self, ip: int, _info):
    #    return str(IPv4Address(ip))
