from typing import Union, dataclass_transform

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column,
                        String,
                        Integer,
                        Boolean,
                        SmallInteger,
                        ForeignKey,
                        Text,
                        TIMESTAMP,
                        SMALLINT,
                        )
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
try:
    from exceptions.loggers import LoggerNames, get_logger
except ImportError:
    from ..exceptions.loggers import LoggerNames, get_logger
from datetime import datetime

from .model_repr import RepresentableBase
try:
    from network_structures import IPv4Struct, PortStruct, ServiceStruct, MacStruct, ObjectStruct, RouteStruct
except ImportError:
    from ..network_structures import IPv4Struct, PortStruct, ServiceStruct, MacStruct, ObjectStruct, RouteStruct

class BaseModel(RepresentableBase):
    """базовый класс для моделей базы данных
    """

    logger = get_logger(LoggerNames.db)  # noqa: F811
            
    def to_dict(self) -> dict:
        """преобразует объект в словарь

        Returns:
            dict: 
        """
        return {i: self.__getattribute__(i).timestamp() if isinstance(self.__getattribute__(i), datetime) else self.__getattribute__(i) for i in self.__table__.c.keys()}
    
    def get_column(self, column_name):
        return self.__table__.c.get(column_name)
    

Base = declarative_base(cls=BaseModel)


class TimeDependent():
    
    created_at: datetime = Column(TIMESTAMP, server_default=func.now())
    updated_at: datetime | None = Column(TIMESTAMP, nullable=True, default=None, 
                                         onupdate=func.now(), server_onupdate=func.now()) # может вызывать проблемы, когда у бд и приложения разное временная зона

@dataclass_transform(kw_only_default=True, field_specifiers=(Column, ))
class NiceInit():
    """
    Миксин для обозначения инита в ide у sql моделей.
    
    ! Важно !
    
    Что бы миксин работал, нужно указать типы классовых переменных
    """
    
class Object(Base, TimeDependent, NiceInit):
    """Модель для таблицы с объектами
    """
    __tablename__ = 'objects'

    id: int = Column(Integer, primary_key=True)
    object_type: str = Column(String(100))
    os: str = Column(String(150))
    status: str = Column(String(30))
    # agent_id = Column(ForeignKey('agents.id'))
    # agent: 'Agent' = relationship('Agent', back_populates='objects', single_parent=True)
    _mac: 'MAC' = relationship('MAC', back_populates='_obj', cascade="all, delete-orphan")
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'os', 'title': 'OS', 'editor': 'input'},
                {'field': 'object_type', 'title': 'Object type', 'editor': 'input'},
                {'field': 'status', 'title': 'Status'},]
        
    def to_struct(self):
        obj = ObjectStruct(
            id=self.id,
            object_type=self.object_type,
            os=self.os,
            status=self.status
        )
        return obj
    
    @classmethod
    def from_struct(self, struct: ObjectStruct):
        
        obj = Object(
            id=struct.id,
            object_type=struct.object_type,
            os=struct.os,
            status=struct.status
        )
        return obj

class ObjectType(Base, NiceInit):
    """Модель для справочника по типам устройств
    """
    __tablename__ = 'object_types'
    id: int = Column(Integer, primary_key=True)
    object_type: str = Column(String(50), nullable=False)
    

class MAC(Base, TimeDependent, NiceInit):
    """Модель для таблицы с мак-адресами
    """
    __tablename__ = 'mac_addresses'

    id: int = Column(Integer, primary_key=True)
    mac: str = Column(String(17))
    object: int = Column(Integer, ForeignKey('objects.id'), nullable=False)
    vendor: str = Column(String)
    _obj: 'Object' = relationship(Object.__name__, back_populates='_mac', lazy='subquery')
    _ip: 'IP' = relationship('IP', back_populates='_mac', cascade='all, delete-orphan')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'object', 'title': 'Object', 'editor': 'list', 'editor_entity': 'object', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'mac', 'title': 'MAC', 'editor': 'input', 'validator': 'required'},
                {'field': 'vendor', 'title': 'Vendor', 'editor': 'input'},]
        
    def to_struct(self):
        mac = MacStruct(
            id=self.id,
            mac=self.mac,
            vendor=self.vendor,
            object= self._obj.to_struct() if self._obj else None
        )
        return mac

    @classmethod
    def from_struct(self, struct: MacStruct):
        mac = MAC(
            id=struct.id,
            mac=str(struct.mac) if struct.mac else None,
            _obj=Object.from_struct(struct.object) if struct.object else None
        )
        return mac

class IP(Base, TimeDependent, NiceInit):
    """Модель для таблицы с ip-адресами
    """
    __tablename__ = 'ip_addresses'

    id: int = Column(Integer, primary_key=True)
    mac: int = Column(Integer, ForeignKey('mac_addresses.id'))
    network_id: int = Column(ForeignKey('networks.id'), nullable=True)
    ip: str = Column(String(15), nullable=False)
    domain_name: str = Column(String(100))
    _mac: 'MAC' = relationship('MAC', back_populates='_ip', lazy='subquery')
    _host_ip: list['Port'] = relationship('Port', back_populates='_ip', cascade='all, delete-orphan', single_parent=False)
    agent: 'Agent' = relationship('Agent', back_populates='ip', single_parent=True, uselist=False)
    
    route_values: list['RouteList'] = relationship('RouteList', back_populates='ip', single_parent=False)
    network: Union['Network',None] = relationship('Network', back_populates='ip_addresses', foreign_keys=[network_id], uselist=False)
    network_if_gateway: Union['Network', None] = relationship('Network', foreign_keys='[Network.gateway_id]', uselist=False)

    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'mac', 'title': 'MAC', 'editor': 'list', 'editor_entity': 'mac', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'ip', 'title': 'IP', 'editor': 'input', 'validator': 'required'},
                # {'field': 'network', 'title': 'NETWORK', 'editor': 'list', 'editor_entity': 'network', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                ]
    
    def to_vis_node(self) -> dict:
        node = {'id': self.id, 'label': self.ip, 'group': '.'.join(self.ip.split('.')[:-1]), 'shape': 'dot', 'value': 1, }
        if obj_type:= self._mac._obj.object_type:
            node.update({'shape': 'image', 'image': f'/static/assets/{obj_type}.svg', 'size': 50})
        return node
    
    def to_struct(self):
        struct = IPv4Struct(
            id=self.id,
            address=self.ip,
            domain_name=self.domain_name,
            ports=[
                i.to_struct() for i in self._host_ip
                ] if self._host_ip else [],
            mac_address= self._mac.to_struct() if self._mac else None,
        )
        return struct
    
    @classmethod
    def from_struct(self, struct: IPv4Struct):
        ip = IP(
            id=struct.id,
            ip=str(struct.address),
            domain_name=struct.domain_name,
            network_id=struct.network_id,
            _host_ip=[Port.from_struct(i) for i in struct.ports] if struct.ports else [],
            _mac=MAC.from_struct(struct.mac_address) if struct.mac_address else MAC(_obj=Object())
        )
        return ip

class Route(Base, NiceInit):
    
    __tablename__ = 'routes'
    
    id: int = Column(Integer, primary_key=True)
    agent_id: int = Column(ForeignKey('agents.id'))
    task_id: int = Column(ForeignKey('tasks.id'))
    
    agent: 'Agent' = relationship('Agent',  back_populates='', single_parent=True)
    routes: list['RouteList'] = relationship('RouteList', back_populates='route', single_parent=False)
    task: 'Task' = relationship('Task' , back_populates='', single_parent=True)
    
    def to_struct(self) -> RouteStruct:
        
        ips = [(i.ip.to_struct(), i.position) for i in self.routes]
        ips = [i[0] for i in sorted(ips, key=lambda x: x[1])]
        route = RouteStruct(id=self.id, agent_id=self.agent_id, routes=ips)
        return route
    
    
class RouteList(Base, NiceInit):
    
    """Список значений 1 роута,
    содержит ссылку на ip и позицию в traceroute
    """
    
    __tablename__ = 'route_lists'
    
    id: int = Column(Integer, primary_key=True)
    route_id: int = Column(ForeignKey('routes.id'))
    value: int = Column(ForeignKey('ip_addresses.id'))
    position: int = Column(Integer)
    
    route: Route = relationship('Route', foreign_keys=[route_id], back_populates='routes')
    ip: IP = relationship('IP', foreign_keys=[value], back_populates='route_values')

# class L3Link(Base, TimeDependent):
#     """Модель для таблицы со связями на l3 уровне
#     """
#     __tablename__ = 'l3_link'

#     id = Column(Integer, primary_key=True)
#     child_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
#     _child_ip = relationship('IP', primaryjoin='IP.id == L3Link.child_ip', back_populates='_child_ip')
#     parent_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
#     _parent_ip = relationship('IP', primaryjoin='IP.id == L3Link.parent_ip', back_populates='_parent_ip')
    
#     @staticmethod
#     def get_headers_for_table() -> list:
#         return [{'field': 'id', 'title': 'ID'},
#                 {'field': 'child_ip', 'title': 'Child IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
#                 {'field': 'parent_ip', 'title': 'Parent IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},]
    
#     def to_vis_edge(self) -> dict:
#         return {'from': self._parent_ip.id, 'to': self._child_ip.id}


class Port(Base, TimeDependent, NiceInit):
    """Модель для таблицы с портами
    """
    __tablename__ = 'ports'

    id: int = Column(Integer, primary_key=True)
    ip: int = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _ip: 'IP' = relationship('IP', back_populates='_host_ip')
    _screenshot: 'Screenshot' = relationship('Screenshot', back_populates='_port')
    port: int = Column(Integer, nullable=False)
    protocol: str = Column(String(10))
    service_name: str = Column(String(100))
    state: str = Column(String(15))
    product: str = Column(String(100))
    extra_info: str = Column(String(150))
    version: str = Column(String(100))
    os_type: str = Column(String(100))
    cpe: str = Column(String(200))
    
    def to_struct(self):
        
        port = PortStruct(
            id=self.id,
            port=self.port,
            protocol=self.protocol,
            state=self.state,
            service=ServiceStruct(
                name=self.service_name,
                product=self.product,
                version=self.version,
                os=self.os_type,
                extra_info=self.extra_info,
                cpe=self.cpe
            )
        )
        return port
    
    @classmethod
    def from_struct(self, port: PortStruct):
        service_data = port.service.model_dump(by_alias=True) if port.service else {}
        port = Port(
            id=port.id,
            port=port.port,
            state=port.state,
            **service_data
        )
        return port
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'port', 'title': 'Port', 'editor': 'input', 'validator': 'required'},
                {'field': 'protocol', 'title': 'Protocol', 'editor': 'input'},
                {'field': 'service_name', 'title': 'Service name', 'editor': 'input'},
                {'field': 'state', 'title': 'State', 'editor': 'input'},
                {'field': 'product', 'title': 'Product', 'editor': 'input'},
                {'field': 'extra_info', 'title': 'Extra info', 'editor': 'input'},
                {'field': 'version', 'title': 'Version', 'editor': 'input'},
                {'field': 'os_type', 'title': 'OS', 'editor': 'input'},
                {'field': 'cpe', 'title': 'CPE', 'editor': 'input'},]


class Task(Base, NiceInit):
    """Модель для таблицы с задачами
    """
    __tablename__ = 'tasks'
    
    id: int = Column(Integer, primary_key=True)
    status: str = Column(String(10))
    # task_type
    created: datetime = Column(TIMESTAMP, server_default=func.now())
    started: datetime = Column(TIMESTAMP)
    finished: datetime = Column(TIMESTAMP)
    params: str = Column(Text)
    comment: str = Column(String)
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'status', 'title': 'Status', 'editor': 'input', 'validator': 'required'},
                {'field': 'created', 'title': 'Created', 'editor': 'datetime'},
                {'field': 'started', 'title': 'Started', 'editor': 'datetime'},
                {'field': 'finished', 'title': 'Finished', 'editor': 'datetime'},
                {'field': 'params', 'title': 'Params', 'editor': 'input'},
                {'field': 'comment', 'title': 'Comment', 'editor': 'input'},]
    

class Screenshot(Base, TimeDependent, NiceInit):
    """Модель для таблицы со скриншотами
    """
    __tablename__ = 'screenshots'
    
    id: int = Column(Integer, primary_key=True)
    port: int = Column(Integer, ForeignKey('ports.id'))
    _port: 'Port' = relationship('Port', back_populates='_screenshot')
    screenshot_path: str = Column(String(100), unique=True)
    task: int = Column(Integer, ForeignKey('tasks.id'))
    _task: 'Task' = relationship('Task', backref='_screenshot')
    domain: str = Column(String)


class Network(Base, TimeDependent, NiceInit):
    
    __tablename__ = 'networks'
    
    id: int = Column(Integer, primary_key=True)
    mask: int = Column(SMALLINT)
    network: str = Column(Text, unique=True)
    gateway_id: int | None = Column(ForeignKey('ip_addresses.id'))
    gateway: IP | None = relationship('IP', uselist=False, foreign_keys=[gateway_id], single_parent=True)
    guess: bool = Column(Boolean, default=True)
    type_id: int = Column(ForeignKey('network_types.id'))
    type: 'NetworkType' = relationship('NetworkType', foreign_keys=[type_id], back_populates='networks')
    ip_addresses: list[IP] = relationship('IP', uselist=True, foreign_keys=[IP.network_id], back_populates='network')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'network', 'title': 'NETWORK'},
            {'field': 'mask', 'title': 'MASK'},
            {'field': 'gateway', 'title': 'GATEWAY'},
            {'field': 'start_ip', 'title': 'START IP'},
            {'field': 'broadcast', 'title': 'BROADCAST'},
            {'field': 'type', 'title': 'TYPE'}, # ! Узнать как сделать выгрузку по вторичным ключам
            ]
        
    
class NetworkType(Base, NiceInit):
    
    __tablename__ = 'network_types'
    
    id: int = Column(Integer, primary_key=True)
    type: str = Column(Text, unique=True)
    
    networks: list[Network] = relationship('Network', back_populates='type', single_parent=False)
    
    
    @classmethod
    def to_create_on_start_up(csl):
        
        to_create = [
            NetworkType(type='internal'),
            NetworkType(type='external')
        ]
        return to_create
    
class Agent(Base, NiceInit):
    
    __tablename__ = 'agents'
    
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)
    description: str = Column(String)
    ip_id: int = Column(ForeignKey('ip_addresses.id'))
    red: int = Column(SmallInteger)
    green: int = Column(SmallInteger)
    blue: int = Column(SmallInteger)
    ip: IP = relationship('IP', back_populates='agent', single_parent=True)
    
    # objects: list['Object'] = relationship('Object', back_populates='agent')
    routes: list['Route'] = relationship('Route', back_populates='agent', single_parent=False)
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'name', 'title': 'NAME'},
            {'field': 'description', 'title': 'DESCRIPTION'},
            {'field': 'color', 'title': 'COLOR'},
            {'field': 'ip', 'title': 'IP'},
            ]
