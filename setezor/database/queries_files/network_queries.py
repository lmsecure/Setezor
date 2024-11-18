from ipaddress import ip_address

from sqlalchemy import func
from sqlalchemy.orm.session import Session

from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from ..models import Network, NetworkType

try:
    from network_structures import NetworkStruct, IPv4Struct, IPv6Struct
except ImportError:
    from ...network_structures import NetworkStruct, IPv4Struct, IPv6Struct

class NetworkQueries(BaseQueries):
    
    model = Network
    
    
    def __init__(self, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        
    @BaseQueries.session_provide
    def create(self, session: Session, **kwargs):
        new_soft_obj = self.model(**kwargs)
        session.add(new_soft_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, kwargs)
        return new_soft_obj

    @BaseQueries.session_provide
    def get_or_create(self, session: Session, to_update: bool = False, **kwargs):
        obj = session.query(self.model).filter(*[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
        if self.check_exists(session=session, query=obj):
            if to_update:
                self.update_by_id(id=obj.first().id, to_update=kwargs)
            self.logger.debug('Get "%s" object with kwargs %s', self.model.__name__, kwargs)
            return obj.first()
        else:
            self.logger.debug('Create new "%s" object with kwargs %s', self.model.__name__, kwargs)
            return self.create(session=session, **kwargs)


    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)
 