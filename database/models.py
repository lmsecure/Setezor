from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from exceptions.loggers import LoggerNames, get_logger
from exceptions.exception_logger import exception_decorator


Base = declarative_base()


class BaseModel:

    logger = get_logger(LoggerNames.db)

    @exception_decorator(LoggerNames.db)
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            fields = [i for i in self.__dir__() if i[0] != '_' and i not in ['id', 'metadata']]
            diff = {}
            for i in fields:
                if not isinstance(self.__getattribute__(i), self.__class__):
                    if self.__getattribute__(i) != other.__getattribute__(i):
                        if other.__getattribute__(i):
                            diff.update({i: other.__getattribute__(i)})
            return diff
        else:
            self.logger.debug(f'Not instanced classes "{self.__class__}" vs "{other.__class__}"')


class Object(Base, BaseModel):
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True)
    object_type = Column(String(100))
    os = Column(String(150))
    status = Column(String(30))


class MAC(Base, BaseModel):
    __tablename__ = 'mac_addresses'

    id = Column(Integer, primary_key=True)
    mac = Column(String(17), nullable=False, unique=True)
    object_id = Column(Integer, ForeignKey('objects.id'))
    obj = relationship('Object', backref='mac')


class IP(Base, BaseModel):
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    mac_id = Column(Integer, ForeignKey('mac_addresses.id'))
    mac = relationship('MAC', backref='ip')
    ip = Column(String(15), nullable=False, unique=True)
    domain_name = Column(String(100))


class L3Link(Base, BaseModel):
    __tablename__ = 'l3_link'

    id = Column(Integer, primary_key=True)
    child_ip_id = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    child_ip = relationship('IP', foreign_keys=child_ip_id)#  backref='child_ip')
    parent_ip_id = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    parent_ip = relationship('IP', foreign_keys=parent_ip_id)#  backref='parent_ip')


class Port(Base, BaseModel):
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True)
    ip_id = Column(Integer, ForeignKey('ip_addresses.id'), nullable=False)
    ip = relationship('IP', backref='host_ip')
    port = Column(Integer, nullable=False)
    service_name = Column(String(100))
    state = Column(String(15))
    product = Column(String(100))
    extra_info = Column(String(150))
    version = Column(String(100))
    os_type = Column(String(100))
    cpe = Column(String(200))
