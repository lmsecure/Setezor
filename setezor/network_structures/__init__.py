from random import randint
from typing import Literal, Any, Annotated, Union
from ipaddress import (
    IPv4Address,
    IPv6Address,
    IPv4Network,
    IPv6Network,
    ip_interface,
    ip_address,
)


from pydantic import (
    BaseModel,
    Field,
    validator,
    field_validator,
    AliasChoices,
    ConfigDict,
    computed_field,
    field_serializer,
    model_serializer,
    model_validator,
    validate_call,
)
from pydantic_extra_types.mac_address import MacAddress

# Можно использовать и классы из ipaddress, создаю отдельный класс, если понадобиться добавить методы в будущем

class BaseStructModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


# todo Разобраться с параметрами global, link_local, loopback, multicast, private, reserved
# todo И как их отобразить в объекте
class IPStruct(BaseStructModel):
    domain_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("domain_name", "domain", "host", "host_name"),
    )
    ports: list["PortStruct"] = Field(default_factory=list)
    mac_address: Union["MacStruct", None] = Field(
        default=None, validation_alias=AliasChoices("mac_addresses", "_mac")
    )

    def __str__(self):
        return str(self.address)

    @validate_call
    def create_network(self, mask: Annotated[int, Field(ge=0, le=32)] = 24):
        return NetworkStruct(network=f"{self.address}/{mask}")


class IPv4Struct(IPStruct):
    address: IPv4Address = Field(
        validation_alias=AliasChoices("address", "ip", "ipaddr", 'addr')
    )

    @model_validator(mode="before")
    def root_validate(cls, values: dict | Any):
        if isinstance(values, str):
            try:
                res = IPv4Address(values)
                return {"address": res}
            except Exception:
                pass
        elif isinstance(values, IPv4Address):
            return {"address": values}
        elif isinstance(values, dict):
            # todo
            ...
        elif hasattr(values, "_mac"):
            values = values.__dict__
            if values["_mac"].mac == "":
                del values["_mac"]
            else:
                values["_mac"] = MacStruct.model_validate(
                    values["_mac"], from_attributes=True, strict=False
                )
            if isinstance(values["ip"], str):
                values["ip"] = IPv4Address(values["ip"])
        return values


class IPv6Struct(IPStruct):
    address: IPv6Address = Field(
        validation_alias=AliasChoices("address", "ip", "ipaddr", 'addr')
    )

    # ! Сейчас вообще не используется
    @model_validator(mode="before")
    def root_validate(cls, values: dict | Any):
        if isinstance(values, str):
            try:
                res = IPv6Address(values)
                return {"address": res}
            except Exception:
                pass
        elif isinstance(values, IPv6Address):
            return {"address": values}
        return values


class AnyIPAddress:
    def __new__(cls, address: object) -> IPv4Struct | IPv6Struct:
        return ip_address(address)


class PortStruct(BaseModel):
    port: int = Field(validation_alias=AliasChoices("value", "port"))
    protocol: Literal["tcp", "udp", None] = "tcp"
    state: Literal["open", "closed", "filtered", "open|filtered", None] = "open"
    service_name: str | None = None


class SoftwareStruct(BaseModel):
    vendor: str | None = None
    product: str | None = None
    type: str | None = None
    version: str | None = None
    build: str | None = None
    patch: str | None = None
    platform: str | None = None
    cpe23: str | None = None
    

class ObjectStruct(BaseStructModel):
    
    object_type: str | None = None
    os: str | None = None
    status: str | None = None

class MacStruct(BaseStructModel):
    mac: MacAddress | None = Field(
        default=None,
        description="Может принимать str формата <xx.xx...> или <xx:xx...>, или число"
    )
    vendor: str | None = None
    addresses: list[IPv4Address | IPv6Address] = Field(default_factory=list)
    object: ObjectStruct | None = None

    @field_validator("mac", mode="before")
    def serialize_mac(mac: str | int):
        if isinstance(mac, int):
            assert mac <= 0xFF_FF_FF_FF_FF_FF and mac > 0
            mac = hex(mac)[2:]
            mac = "".join(("0" for i in range(12 - len(mac)))) + mac
            tmp = []
            start = 0
            for _ in range(6):
                tmp.append(mac[start : start + 2])
                start += 2
            return ":".join(tmp)
        return mac

    @validator("vendor")
    def validate_options(cls, value, values):
        # todo
        return value

    def __int__(self):
        return int(self.mac.translate({":": ""}, base=16))


class NetworkStruct(BaseStructModel):
    network: IPv4Network | IPv6Network
    gateway: IPv4Struct | IPv6Struct | None = None
    _as: str | None = None
    ip_address: list[IPv4Struct | IPv6Struct] = Field(
        default_factory=list, validation_alias=AliasChoices("ip_addresses", "ip")
    )

    @computed_field
    @property
    def mask(self) -> int:
        return self.network._prefixlen

    @computed_field
    @property
    def type(self) -> Literal["external", "internal"]:
        if self.network.is_global:
            return "external"
        else:
            return "internal"

    @computed_field
    @property
    def broadcast(self) -> int:
        """
        Широковещательный адрес

        :return: Широковещательный адрес
        :rtype: int
        """
        return int(self.network.broadcast_address)

    @computed_field
    @property
    def start_ip(self) -> int:
        """
        :return: Значение ip, с которого начинается сеть
        :rtype: int
        """
        return int(self.network.network_address)

    @field_validator("network", mode="before")
    def validate_network(value):
        # todo!!! узнать как валидировать маску!
        return ip_interface(value).network

    @validate_call
    def check_address(self, address: IPv4Struct | IPv6Struct) -> bool:
        return address.address in self.network


def random_color() -> int:
    return randint(0, 255)


class AgentStruct(BaseStructModel):
    name: str
    description: str = Field(default="")
    ip: IPv4Struct | IPv6Struct | None = None
    red: int = Field(
        ge=0,
        le=255,
        default_factory=random_color,
        validation_alias=AliasChoices("red", "r"),
    )
    green: int = Field(
        ge=0,
        le=255,
        default_factory=random_color,
        validation_alias=AliasChoices("green", "g"),
    )
    blue: int = Field(
        ge=0,
        le=255,
        default_factory=random_color,
        validation_alias=AliasChoices("blue", "b"),
    )


class InterfaceStruct(BaseStructModel):
    id: str | None = None
    name: str
    ip: str | None = None
    ip_id: str | None = None
    mac: str | None = None
    
    
class RouteStruct(BaseStructModel):
    
    """Структура роутов"""
    
    agent_id: str
    routes: list[IPv4Struct] = Field(min_length=2)