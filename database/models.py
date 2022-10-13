from asyncio.log import logger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from exceptions.loggers import LoggerNames, get_logger
from exceptions.exception_logger import exception_decorator

# class Base(object):
#     @classmethod
#     def __table_cls__(cls, *args, **kwargs):
#         t = Table(*args, **kwargs)
#         t.decl_class = cls
#         return t

# Base = declarative_base(cls=Base)


class BaseModel:
    """базовый класс для моделей базы данных
    """

    logger = get_logger(LoggerNames.db)

    @exception_decorator(LoggerNames.db)
    def __eq__(self, other):
        if other is None:
            return {}
        if isinstance(other, self.__class__):
            fields = [i for i in self.__dir__() if i[0] != '_' and i not in ['id', 'metadata'] and not isinstance(self.__getattribute__(i), self.__class__)]
            diff = {}
            for i in fields:
                if self.__getattribute__(i) != other.__getattribute__(i) and other.__getattribute__(i):
                    diff.update({i: other.__getattribute__(i)})
            logger.debug(f"Find difference in {self.__class__.__name__} objects\n" +
                         f"OLD: {', '.join([f'{i}: {self.__getattribute__(i)}' for i in fields])}\n" +
                         f"NEW: {', '.join([f'{i}: {other.__getattribute__(i)}' for i in fields])}\n" +
                         f"DIFF: {diff}")
            return diff
        else:
            self.logger.debug(f'Not instanced classes "{self.__class__}" vs "{other.__class__}"')
            
    def to_dict(self) -> dict:
        """преобразует объект в словарь

        Returns:
            dict: 
        """
        return {i: self.__getattribute__(i) for i in self.__table__.c.keys()}
    
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
    _mac = relationship('MAC', back_populates='_obj')


class MAC(Base):
    """Модель для таблицы с мак-адресами
    """
    __tablename__ = 'mac_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(String(17))
    object = Column(Integer, ForeignKey('objects.id'))
    _obj = relationship(Object.__name__, back_populates='_mac')
    _ip = relationship('IP', back_populates='_mac')
    
    def to_dict(self) -> dict:
        """преобразует объект в словарь, подменяя индексы на значения

        Returns:
            dict: 
        """
        return {'id': self.id, 'mac': self.mac, } # FixMe 'object': self._obj.id} 


class IP(Base):
    """Модель для таблицы с ip-адресами
    """
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(Integer, ForeignKey('mac_addresses.id'))
    _mac = relationship('MAC', back_populates='_ip')
    ip = Column(String(15), nullable=False)
    domain_name = Column(String(100))
    _host_ip = relationship('Port', back_populates='_ip')
    
    def to_dict(self) -> dict:
        """преобразует объект в словарь, подменяя индексы на значения

        Returns:
            dict: 
        """
        return {'id': self.id, 'ip': self.ip, 'mac': self._mac.mac, 'domain_name': self.domain_name}


class L3Link(Base):
    """Модель для таблицы со связями на l3 уровне
    """
    __tablename__ = 'l3_link'

    id = Column(Integer, primary_key=True)
    child_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _child_ip = relationship('IP', foreign_keys=child_ip)
    parent_ip = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    _parent_ip = relationship('IP', foreign_keys=parent_ip)
    
    def to_dict(self) -> dict:
        """преобразует объект в словарь, подменяя индексы на значения

        Returns:
            dict: 
        """
        return {'id': self.id, 'child_ip': self._child_ip.ip, 'parent_ip': self._parent_ip.ip}


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
    
    def to_dict(self) -> dict:
        """преобразует объект в словарь, подменяя индексы на значения

        Returns:
            dict: 
        """
        return {'id': self.id, 'ip': self._ip.ip, 'port': self.port, 'protocol': self.protocol, 'service_name': self.service_name, 'state': self.state,
                'product': self.product, 'extra_info': self.extra_info, 'version': self.version, 'os_type': self.os_type, 'cpe': self.cpe}


class Task(Base):
    """Модель для таблицы с задачами
    """
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(10))
    created = Column(DateTime, server_default=func.now())
    started = Column(DateTime)
    finished = Column(DateTime)
    params = Column(Text)
    comment = Column(String)    
    

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
    
    def to_dict(self) -> dict:
        """преобразует объект в словарь, подменяя индексы на значения

        Returns:
            dict: 
        """
        return {'id': self.id, 'port': self.port, 'screenshot_path': self.screenshot_path, 'task': self.task, 'domain': self.domain}