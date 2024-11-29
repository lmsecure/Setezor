import ipaddress

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
    def get_or_create(self, session: Session, ip: str, mask: int, type_id: int, to_update: bool = False, **kwargs):

        if not mask: mask = 24
        network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
        data = {
            "mask" : mask,
            "network" : str(network),
            "start_ip" : str(network.network_address),
            "broadcast" : str(network.broadcast_address),
            "type_id" : type_id}

        obj = session.query(self.model).filter(*[self.model.__table__.c.get(k) == v for k, v in data.items() if v])
        if self.check_exists(session=session, query=obj):
            if to_update:
                self.update_by_id(id=obj.first().id, to_update=data)
            self.logger.debug('Get "%s" object with data %s', self.model.__name__, data)
            return obj.first()
        else:
            self.logger.debug('Create new "%s" object with data %s', self.model.__name__, data)
            return self.create(session=session, **data)


    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)
 