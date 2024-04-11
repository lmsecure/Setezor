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
    def create_from_addresses(self, session: Session, *, addresses: list[IPv4Struct]):
        
        """Получает из бд или создает подсети из адресов и связывает их"""
        
        for addr in addresses:
            with session.no_autoflush:
                db_addr = session.query(IP).where(IP.ip == str(addr)).first()
                if not db_addr:
                    if addr.mac_addresses:
                        mac = str(addr.mac_addresses)
                    else:
                        mac = None
                    db_addr = self.ip_queries.create(session, ip=str(addr), mac=mac, domain_name=addr.domain_name)
                net = addr.create_network()
                db_net = self.get_network(session, network=net) 
                if not db_net:
                    db_net = self.create(session, network=net)
                
                db_addr.network_id = db_net.id
                session.add(db_addr)
    
    @BaseQueries.session_provide
    def __define_supper_net(self, session: Session, *, network: NetworkStruct):
        """
        Определяет сеть, в которую входит подсеть. При нахождении, 
        записывает в бд ссылку и возвращает объект NetworkStruct

        :param session: сессия алхимии
        :param network: объект нетворка
        """
        query = session.query(Network, func.min(Network.broadcast)).where(Network.start_ip < network.start_ip,
                                        Network.broadcast > network.broadcast)
        res = query.first()
        if supper_net:= res[0]:
            net = self.get_network(session, network=network)
            net.supper_net_id = supper_net.id
            
    @BaseQueries.session_provide
    def get_subnets(self, session: Session, *, network: NetworkStruct) ->  list[Network]:
        """
        Возвращает подсети для принимаемого нетворка

        :param session: Сессия алхимии
        :param network: Объект нетворка, у которого будут искаться дети
        :raises ValueError: Возбуждается, если нет указанного нетворка
        :return: _description_
        """
        db_net = self.get_network(session, network=network)
        if not db_net:
            raise ValueError(f'Network {network} does not exist in database!')
        
        res = session.query(Network).where(Network.supper_net_id == db_net.id).all()
        return res
    
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
            return db_net
        
        db_net = Network(
            mask=network.mask,
            network=str(network.network) if network.network else None,
            gateway=str(network.gateway) if network.gateway else None,
            broadcast=network.broadcast,
            start_ip=network.start_ip,
            type_id=1 if network.type == 'internal' else 2
        )
        session.add(db_net)
        session.commit()
        self.__define_supper_net(session, network=network)
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
    
    
    # Методы для получения в api
    @BaseQueries.session_provide
    def get_root_networks(self, session: Session):
        """
        Метод получения структур нетворка без родителей, 
        должен вызываться первым при построении карты

        :param session: Сессия алхимии
        :return: Список заполненных структур
        """
        networks = session.query(Network).where(Network.supper_net_id == None).all()  # noqa: E711
        res: list[NetworkStruct] = []
        for db_net in networks:
            net = NetworkStruct.model_validate(db_net, from_attributes=True, strict=False)
            res.append(net)
        return res
    
    
    @BaseQueries.session_provide
    def get_subnets_structs(self, session: Session, network: NetworkStruct) -> list[NetworkStruct]:
        """
        Возвращает заполненные структуры подсетей

        :param session: Сессия алхимии
        :param network: Сеть, у которой будут найдены подсети
        :return: Список подсетей
        """
        networks = self.get_subnets(session, network=network)
        networks = [NetworkStruct.model_validate(i, from_attributes=True, strict=True) for i in networks]
        return networks
    
    
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