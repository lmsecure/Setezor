from ipaddress import ip_address

from sqlalchemy import func
from sqlalchemy.orm.session import Session

from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from ..models import Network, NetworkType, IP

try:
    from network_structures import NetworkStruct, IPv4Struct, IPv6Struct
except ImportError:
    from ...network_structures import NetworkStruct, IPv4Struct, IPv6Struct

from .ip_queries import IPQueries

class NetworkQueries(BaseQueries):
    
    model = Network
    
    
    def __init__(self, ip_queries: IPQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.ip_queries = ip_queries
        
    @BaseQueries.session_provide
    def attach_addresses(self, session: Session, *, network: NetworkStruct):
        """
        Для все адресов, не имеющих нетворка и, входящих в эту подсеть, 
        будет вставлена ссылка на нетворк

        :param session: Сессия алхимии
        :param network: Объект нетворка, к которого будут подвязываться адреса
        :raises ValueError: Возбуждается, если нет указанного нетворка
        """
        db_net = self.get_network(session, network=network)
        if not db_net:
            raise ValueError(f'Network {network} does not exist in database!')
        
        addresses: list[IP] = session.query(IP).where(IP.network_id == None).all()  # noqa: E711
        for addr in addresses:
            int_addr = int(ip_address(addr.ip))
            if (int_addr >= db_net.start_ip and int_addr <= db_net.broadcast):
                addr.network_id = db_net.id
    
    @BaseQueries.session_provide
    def create(self, session: Session, *, network: NetworkStruct):
        """
        Создание объекта в бд по принимаемой структуре,

        :param session: Сессия алхимии
        :param network: Структура нетворка
        :return: Возвращает объект из бд
        """
        db_net = session.query(Network).where(Network.network == str(network.network)).first()
        if db_net:
            raise ValueError(f'Network <{str(network.network)}> exists in database!')
        
        if network.gateway.address.is_global:
            raise ValueError(f'Network gateway <{network.gateway}> must be local')
        
        
        db_ip = session.query(IP).where(IP.ip == str(network.gateway)).first()
        if not db_ip:
            db_ip = self.ip_queries.create(session=session, ip=str(network.gateway), 
                                           domain_name=network.gateway.domain_name)
        db_net = Network(
            mask=network.mask,
            network=str(network.network),
            gateway=db_ip,
            type_id=1 if network.type == 'internal' else 2 # fixme
        )
        session.add(db_net)
        session.flush()
        self.logger.debug('Created "%s" with kwargs %s', self.model.__name__, network.model_dump())
        return db_net
    
    
    @BaseQueries.session_provide
    def get_network(self, session: Session, *, network: NetworkStruct) -> Network | None:
        
        '''Возвращает нетворк из бд, если указать `with_addresses`, то будут подгружены адреса'''
        
        res = session.query(Network).where(Network.network == str(network.network)).first()
        if res:
            return res
    
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'network', 'type': '', 'required': True},
                {'name': 'mask', 'type': '', 'required': True},
                {'name': 'gateway', 'type': '', 'required': True},
                {'name': 'broadcast', 'type': '', 'required': True},
                {'name': 'broadcast', 'type': '', 'required': True},
                {'name': 'type', 'type': '', 'required': True}]
    
    
    @BaseQueries.session_provide
    def edit(self, session: Session, *, old_network: NetworkStruct, new_network: NetworkStruct):
        
        """Меняет нетвор к вб, вместе с этим будут отвязаны/связаны ip"""
        
        db_net = self.get_network(session, network=old_network)
        if not db_net:
            raise ValueError(f'Network {old_network} does not exist in database!')
        
        db_new_net = self.get_network(session, network=new_network)
            
    @BaseQueries.session_provide
    def delete(self, session: Session, *, network: NetworkStruct, with_addresses: bool = False):
        
        db_net = self.get_network(session, network=network)
        if not db_net:
            raise ValueError(f'Network {network} does not exist in database!')
        
        ...