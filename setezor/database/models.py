from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column,
                        String,
                        Integer,
                        SmallInteger,
                        ForeignKey,
                        Text,
                        TIMESTAMP, BOOLEAN, JSON,
                        SMALLINT,
                        DateTime,
                        Float
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
    from network_structures import IPv4Struct, PortStruct, MacStruct, ObjectStruct, RouteStruct
except ImportError:
    from ..network_structures import IPv4Struct, PortStruct, MacStruct, ObjectStruct, RouteStruct

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
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, default=None, 
                                         onupdate=func.now(), server_onupdate=func.now()) # может вызывать проблемы, когда у бд и приложения разное временная зона

class Object(Base, TimeDependent):
    """Модель для таблицы с объектами
    """
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True)
    object_type = Column(String(100))
    os = Column(String(150))
    status = Column(String(30))
    # agent_id = Column(ForeignKey('agents.id'))
    # agent: 'Agent' = relationship('Agent', back_populates='objects', single_parent=True)
    _mac = relationship('MAC', back_populates='_obj', cascade="all, delete-orphan")
    
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


class ObjectType(Base):
    """Модель для справочника по типам устройств
    """
    __tablename__ = 'object_types'
    id = Column(Integer, primary_key=True)
    object_type = Column(Text, nullable=False)
    
    
class MAC(Base, TimeDependent):
    """Модель для таблицы с мак-адресами
    """
    __tablename__ = 'mac_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(String(17))
    object = Column(Integer, ForeignKey('objects.id'), nullable=False)
    vendor = Column(String)
    _obj = relationship(Object.__name__, back_populates='_mac', lazy='subquery')
    _ip = relationship('IP', back_populates='_mac', cascade='all, delete-orphan')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'object', 'title': 'Object', 'editor': 'list', 'editor_entity': 'object', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'mac', 'title': 'MAC', 'editor': 'input', 'validator': 'required'},
                {'field': 'vendor', 'title': 'Vendor', 'editor': 'input'},]
        
    @classmethod
    def get_name(cls):
        return cls.__name__.lower()


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

class IP(Base, TimeDependent):
    """Модель для таблицы с ip-адресами
    """
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(Integer, ForeignKey('mac_addresses.id'))
    network_id = Column(ForeignKey('networks.id'))
    ip = Column(String(15), nullable=False)
    domain_name = Column(String(100))
    network = relationship('Network', back_populates='ip_addresses', single_parent=True)
    _mac = relationship('MAC', back_populates='_ip', lazy='subquery')
    _host_ip = relationship('Port', back_populates='_ip', cascade='all, delete-orphan', single_parent=False)
    agent = relationship('Agent', back_populates='ip', single_parent=True)

    _ip_id = relationship('Domain', back_populates='_ip_id')
    _child_ip = relationship('L3Link', primaryjoin='IP.id == L3Link.child_ip', back_populates='_child_ip', cascade='all, delete-orphan')
    _parent_ip = relationship('L3Link', primaryjoin='IP.id == L3Link.parent_ip', back_populates='_parent_ip', cascade='all, delete-orphan')
    _cert = relationship('Cert', back_populates = '_ip_id')
    _whois = relationship('Whois', back_populates = '_ip_id')
    _resource = relationship('Resource', back_populates = '_ip_id')

    
    route_values = relationship('RouteList', back_populates='ip', single_parent=False)

    @classmethod
    def get_name(cls):
        return cls.__name__.lower()

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
            _host_ip=[Port.from_struct(i) for i in struct.ports] if struct.ports else [],
            _mac=MAC.from_struct(struct.mac_address) if struct.mac_address else MAC(_obj=Object())
        )
        return ip
        
class Route(Base):
    
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    agent_id: int = Column(ForeignKey('agents.id'))
    task_id: int = Column(ForeignKey('tasks.id'))
    
    agent= relationship('Agent',  back_populates='', single_parent=True)
    routes = relationship('RouteList', back_populates='route', single_parent=False)
    task = relationship('Task' , back_populates='', single_parent=True)
    
    def to_struct(self) -> RouteStruct:
        
        ips = [(i.ip.to_struct(), i.position) for i in self.routes]
        ips = [i[0] for i in sorted(ips, key=lambda x: x[1])]
        route = RouteStruct(id=self.id, agent_id=self.agent_id, routes=ips)
        return route
    
    
class RouteList(Base):
    
    """Список значений 1 роута,
    содержит ссылку на ip и позицию в traceroute
    """
    
    __tablename__ = 'route_lists'
    
    id = Column(Integer, primary_key=True)
    route_id = Column(ForeignKey('routes.id'))
    value: int = Column(ForeignKey('ip_addresses.id'))
    position: int = Column(Integer)
    
    route = relationship('Route', foreign_keys=[route_id], back_populates='routes')
    ip = relationship('IP', foreign_keys=[value], back_populates='route_values')

class L3Link(Base):
    """Модель для таблицы со связями на l3 уровне
    """
    __tablename__ = 'l3_link'

    id = Column(Integer, primary_key=True)
    child_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _child_ip = relationship('IP', primaryjoin='IP.id == L3Link.child_ip', back_populates='_child_ip')
    parent_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _parent_ip = relationship('IP', primaryjoin='IP.id == L3Link.parent_ip', back_populates='_parent_ip')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'child_ip', 'title': 'Child IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'parent_ip', 'title': 'Parent IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},]
    
    def to_vis_edge(self) -> dict:
        return {'from': self._parent_ip.id, 'to': self._child_ip.id}


class Port(Base, TimeDependent):
    """Модель для таблицы с портами
    """
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True)
    ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _ip = relationship('IP', back_populates='_host_ip')
    _screenshot = relationship('Screenshot', back_populates='_port')
    _cert = relationship('Cert', back_populates = '_port')
    port = Column(Integer, nullable=False)
    protocol = Column(String(10))
    service_name = Column(String(100))
    state = Column(String(15))
    _resource = relationship('Resource', back_populates = '_port_id')
    
    def to_struct(self):
        
        port = PortStruct(
            id=self.id,
            port=self.port,
            protocol=self.protocol,
            service_name=self.service_name,
            state=self.state
        )
        return port
    
    @classmethod
    def from_struct(self, port: PortStruct):
        port = Port(
            id=port.id,
            port=port.port,
            state=port.state,
            service_data=port.service_name
        )
        return port
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'ip', 'title': 'IP', 'editor': 'list', 'editor_entity': 'ip', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'port', 'title': 'Port', 'editor': 'input', 'validator': 'required'},
                {'field': 'protocol', 'title': 'Protocol', 'editor': 'input'},
                {'field': 'service_name', 'title': 'Service name', 'editor': 'input'}]

    @classmethod
    def get_name(cls):
        return cls.__name__.lower()

class Task(Base):
    """Модель для таблицы с задачами
    """
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(10))
    # task_type
    created = Column(TIMESTAMP, server_default=func.now())
    started = Column(TIMESTAMP)
    finished = Column(TIMESTAMP)
    params = Column(Text)
    comment = Column(String)
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'status', 'title': 'Status', 'editor': 'input', 'validator': 'required'},
                {'field': 'created', 'title': 'Created', 'editor': 'datetime'},
                {'field': 'started', 'title': 'Started', 'editor': 'datetime'},
                {'field': 'finished', 'title': 'Finished', 'editor': 'datetime'},
                {'field': 'params', 'title': 'Params', 'editor': 'input'},
                {'field': 'comment', 'title': 'Comment', 'editor': 'input'},]
    
    @classmethod
    def get_name(cls):
        return cls.__name__.lower()

class Screenshot(Base, TimeDependent):
    """Модель для таблицы со скриншотами
    """
    __tablename__ = 'screenshots'
    
    id = Column(Integer, primary_key=True)
    port = Column(Integer, ForeignKey('ports.id'))
    _port = relationship('Port', back_populates='_screenshot')
    screenshot_path = Column(String(100), unique=True)
    task = Column(Integer, ForeignKey('tasks.id'))
    _task = relationship('Task', backref='_screenshot')
    domain = Column(String)

        
class Network(Base, TimeDependent):
    
    __tablename__ = 'networks'
    
    id = Column(Integer, primary_key=True)
    mask = Column(SMALLINT)
    network = Column(Text, unique=True)
    start_ip = Column(Integer, nullable=False)
    broadcast = Column(Integer, nullable=False)
    gateway = Column(Integer, nullable=True)
    # _as = Column(Text)
    type_id = Column(ForeignKey('network_types.id'))
    type = relationship('NetworkType', back_populates='networks', single_parent=True)
    supper_net_id = Column(ForeignKey('networks.id'))
    
    # whois = Column()
    ip_addresses = relationship('IP', back_populates='network', single_parent=True)
    
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
    
    
class NetworkType(Base):
    
    __tablename__ = 'network_types'
    
    id = Column(Integer, primary_key=True)
    type = Column(Text, unique=True)
    
    networks = relationship('Network', back_populates='type', single_parent=False)
    
    
    @classmethod
    def to_create_on_start_up(csl):
        
        to_create = [
            NetworkType(type='internal'),
            NetworkType(type='external')
        ]
        return to_create
    
class Agent(Base):
    
    __tablename__ = 'agents'
    
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)
    description: str = Column(String)
    ip_id: int = Column(ForeignKey('ip_addresses.id'))
    red: int = Column(SmallInteger)
    green: int = Column(SmallInteger)
    blue: int = Column(SmallInteger)
    ip = relationship('IP', back_populates='agent', single_parent=True)
    
    # objects: list['Object'] = relationship('Object', back_populates='agent')
    routes = relationship('Route', back_populates='agent', single_parent=False)
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'name', 'title': 'NAME'},
            {'field': 'description', 'title': 'DESCRIPTION'},
            {'field': 'color', 'title': 'COLOR'},
            {'field': 'ip', 'title': 'IP'},
            ]
        
        
class Domain(Base):
    """Модель для таблицы с доменами
    """
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    domain = Column(String)
    ip_id = Column(Integer, ForeignKey('ip_addresses.id'))
    _ip_id = relationship('IP', back_populates='_ip_id')
    is_wildcard = Column(BOOLEAN)
    _dns = relationship('DNS', back_populates = '_domain_id')
    _cert = relationship('Cert', back_populates = '_domain_id')
    _whois = relationship('Whois', back_populates = '_domain_id')
    _resource = relationship('Resource', back_populates = '_domain_id')

    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'domain', 'title': 'domain', 'editor': 'input'},
                {'field': 'ip_id', 'title': 'ip_id', 'editor': 'input'},
                {'field': 'is_wildcard', 'title': 'is_wildcard'}
                ]
    
    
class DNS(Base):
    """Модель для таблицы с доменами
    """
    __tablename__ = 'dns'
        
    id = Column(Integer, primary_key=True)
    

    domain_id = Column(Integer, ForeignKey('domains.id'))
    _domain_id = relationship('Domain', back_populates='_dns')
    
    record_type = Column(String(6))
    record_value = Column(String)
    
class Cert(Base):
    
    __tablename__ = 'cert'
    
    id = Column(Integer, primary_key=True)
    
    ip_id = Column(Integer, ForeignKey('ip_addresses.id'))
    _ip_id = relationship('IP', back_populates='_cert')
    
    domain_id = Column(Integer, ForeignKey('domains.id'))
    _domain_id = relationship('Domain', back_populates='_cert')
    
    port = Column(Integer, ForeignKey('ports.id'))
    _port = relationship('Port', back_populates='_cert')
    
    data = Column(JSON)
    not_before_date = Column(DateTime)
    not_after_date = Column(DateTime)
    is_expired = Column(BOOLEAN)
    alt_name = Column(String)


class Whois(Base):
    
    __tablename__ = 'whois'
    
    id = Column(Integer, primary_key = True)
    
    ip_id = Column(Integer, ForeignKey('ip_addresses.id'))
    _ip_id = relationship('IP', back_populates='_whois')
    
    domain_id = Column(Integer, ForeignKey('domains.id'))
    _domain_id = relationship('Domain', back_populates='_whois')
    
    domain_crt = Column(String)
    data = Column(JSON)
    org_name = Column(String)
    AS = Column(String)
    range_ip =  Column(String)
    netmask = Column(Integer)



'''
class SoftType(Base):
    __tablename__ = 'soft_type'

    id = Column(Integer, primary_key=True)
    name = Column(String)
'''

class Software(Base):
    __tablename__ = "software"

    id = Column(Integer, primary_key=True)
    vendor = Column(String)
    product = Column(String)
    type = Column(String)
    version = Column(String)
    build = Column(String)
    patch = Column(String)
    platform = Column(String)
    cpe23 = Column(String)

    _resource = relationship('Resource_Software',back_populates='_software')

class Resource(Base):
    __tablename__ = 'resource'

    id = Column(Integer, primary_key=True)

    ip_id = Column(Integer, ForeignKey('ip_addresses.id'))
    _ip_id = relationship('IP', back_populates='_resource')
    
    domain_id = Column(Integer, ForeignKey('domains.id'))
    _domain_id = relationship('Domain', back_populates='_resource')

    port_id = Column(Integer, ForeignKey('ports.id'))
    _port_id = relationship('Port', back_populates='_resource')

    acunetix_id = Column(String(36), unique=True)
    
    _software = relationship('Resource_Software', back_populates='_resource')


class Resource_Software(Base):
    __tablename__ = "resource_software"

    id = Column(Integer, primary_key=True)

    resource_id = Column(Integer,ForeignKey('resource.id'))
    _resource = relationship('Resource', back_populates='_software')

    software_id = Column(Integer, ForeignKey('software.id'))
    _software = relationship('Software', back_populates='_resource')

    _vulnerability = relationship('Vulnerability_Resource_Soft',back_populates="_resource_soft")

class Vulnerability_Resource_Soft(Base):
    __tablename__ = "vulnerability_resource_soft"
    id = Column(Integer, primary_key=True)

    vulnerability_id = Column(Integer, ForeignKey('vulnerabilities.id'))
    _vulnerability = relationship('Vulnerability', back_populates='_resource_soft')

    resource_soft_id = Column(Integer, ForeignKey('resource_software.id'))
    _resource_soft = relationship('Resource_Software', back_populates='_vulnerability')


class Vulnerability(Base):
    __tablename__ = 'vulnerabilities'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    cve = Column(String)
    cwe = Column(String)
    description = Column(String)
    details = Column(String)
    cvss = Column(String)
    cvss2 = Column(String)
    cvss2_score = Column(Float)
    cvss3 = Column(String)
    cvss3_score = Column(Float)
    cvss4 = Column(String)
    cvss4_score = Column(Float)
    severity = Column(Integer)
    _resource_soft = relationship("Vulnerability_Resource_Soft",back_populates="_vulnerability")
    _link = relationship("VulnerabilityLink", back_populates="_vulnerability")

    @classmethod
    def from_struct(self, struct: MacStruct):
        vuln = Vulnerability(**struct)
        return vuln
    

class VulnerabilityLink(Base):
    __tablename__ = 'vulnerability_links'

    id = Column(Integer, primary_key=True)
    link = Column(String)
    vulnerability_id = Column(Integer,ForeignKey("vulnerabilities.id"))
    _vulnerability = relationship("Vulnerability", back_populates="_link")