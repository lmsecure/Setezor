from asyncio.log import logger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from exceptions.loggers import LoggerNames, get_logger
from datetime import datetime


class BaseModel:
    """базовый класс для моделей базы данных
    """

    logger = get_logger(LoggerNames.db)
            
    def to_dict(self) -> dict:
        """преобразует объект в словарь

        Returns:
            dict: 
        """
        return {i: self.__getattribute__(i).timestamp() if isinstance(self.__getattribute__(i), datetime) else self.__getattribute__(i) for i in self.__table__.c.keys()}
    
    def get_column(self, column_name):
        return self.__table__.c.get(column_name)


Base = declarative_base(cls=BaseModel)

class Object(Base):
    """Модель для таблицы с объектами
    """
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True)
    object_type = Column(String(100))
    os = Column(String(150))
    status = Column(String(30))
    _mac = relationship('MAC', back_populates='_obj', cascade="all, delete-orphan")
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'os', 'title': 'OS', 'editor': 'input'},
                {'field': 'object_type', 'title': 'Object type', 'editor': 'input'},#, 'formatter': ''},
                {'field': 'status', 'title': 'Status'},]

class ObjectType(Base):
    """Модель для справочника по типам устройств
    """
    __tablename__ = 'object_types'
    id = Column(Integer, primary_key=True)
    object_type = Column(String(50), nullable=False)
    
    
class MAC(Base):
    """Модель для таблицы с мак-адресами
    """
    __tablename__ = 'mac_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(String(17))
    object = Column(Integer, ForeignKey('objects.id'), nullable=False)
    vendor = Column(String)
    _obj = relationship(Object.__name__, back_populates='_mac')
    _ip = relationship('IP', back_populates='_mac', cascade='all, delete-orphan')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'object', 'title': 'Object', 'editor': 'list', 'editor_entity': 'object', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'mac', 'title': 'MAC', 'editor': 'input', 'validator': 'required'},
                {'field': 'vendor', 'title': 'Vendor', 'editor': 'input'},]


class IP(Base):
    """Модель для таблицы с ip-адресами
    """
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(Integer, ForeignKey('mac_addresses.id'))
    _mac = relationship('MAC', back_populates='_ip')
    ip = Column(String(15), nullable=False)
    domain_name = Column(String(100))
    _host_ip = relationship('Port', back_populates='_ip', cascade='all, delete-orphan')
    _child_ip = relationship('L3Link', primaryjoin='IP.id == L3Link.child_ip', back_populates='_child_ip', cascade='all, delete-orphan')
    _parent_ip = relationship('L3Link', primaryjoin='IP.id == L3Link.parent_ip', back_populates='_parent_ip', cascade='all, delete-orphan')
    
    @staticmethod
    def get_headers_for_table() -> list:
        return [{'field': 'id', 'title': 'ID'},
                {'field': 'mac', 'title': 'MAC', 'editor': 'list', 'editor_entity': 'mac', 'formatter': 'foriegnKeyReplace', 'validator': 'required'},
                {'field': 'ip', 'title': 'IP', 'editor': 'input', 'validator': 'required'},]
    
    def to_vis_node(self) -> dict:
        node = {'id': self.id, 'label': self.ip, 'group': '.'.join(self.ip.split('.')[:-1]), 'shape': 'dot', 'value': 1, }
        if obj_type:= self._mac._obj.object_type:
            node.update({'shape': 'image', 'image': f'/static/assets/{obj_type}.svg', 'size': 50})
        return node


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


class Port(Base):
    """Модель для таблицы с портами
    """
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True)
    ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _ip = relationship('IP', back_populates='_host_ip')
    _screenshot = relationship('Screenshot', back_populates='_port')
    port = Column(Integer, nullable=False)
    protocol = Column(String(10))
    service_name = Column(String(100))
    state = Column(String(15))
    product = Column(String(100))
    extra_info = Column(String(150))
    version = Column(String(100))
    os_type = Column(String(100))
    cpe = Column(String(200))
    
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
    

class Screenshot(Base):
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