from typing import TYPE_CHECKING, Union
from ipaddress import IPv4Address, IPv4Interface
from functools import lru_cache

from sqlalchemy.orm.session import Session
from ..models import IP, MAC, Object, Port, Network
from ..queries_files.base_queries import Mock, BaseQueries
from ..queries_files.mac_queries import MACQueries

try:
    from network_structures import IPv4Struct, RouteStruct
except ImportError:
    from ...network_structures import IPv4Struct, RouteStruct

if TYPE_CHECKING:
    from .route_queries import RouteQueries

class IPQueries(BaseQueries):
    """Класс запросов к таблице IP адресов
    """    
    
    model = IP
    
    def __init__(self, session_maker: Session, mac: MACQueries,
                 route_queries: Union[None,'RouteQueries'] = None):
        """Инициализация объекта запросов

        Args:
            session_maker (Session): генератор сессий
            mac (MACQueries): объект запросов к таблице с mac адресами
            route_queries: объект запросов к роутам, нужно инициализировать позже!
        """        
        super().__init__(session_maker)
        self.mac = mac
        self.route_queries = route_queries
    
    @lru_cache
    def _get_ip_gateway(self, ip: str, mask: int = 24):
        """
        Возвращает адресс гетвея (1 адресс в сети)

        :param ip: ip
        :param mask: маска для сети, defaults to 24
        :raises ValueError: Возбуждается, если непрвильная маска
        :return: гетвей
        """
        if mask > 32:
            raise ValueError('Mask can not be more than 32')
        if mask < 0:
            raise ValueError('Mask must be more than 0')

        addr = IPv4Interface(ip + f'/{mask}')
        gateway = addr.network.network_address + 1
        return gateway
    
    @lru_cache()
    def ___get_ip_net(self, ip: str, mask: int = 24):
        net = IPv4Interface(ip + f'/{mask}').network
        return net
        
        
    @BaseQueries.session_provide
    def create(self, session: Session, ip: str, mac: str=None, 
               domain_name: str=None, **kwargs):
        """Метод создания объекта IP адреса

        Args:
            session (Session): сессия коннекта к базе
            ip (str): ip адрес
            mac (str, optional): mac адрес. Defaults to None.
            domain_name (str, optional): доменное имя. Defaults to None.

        Returns:
            _type_: объект ip адреса
        """
        mac_obj = self.mac.create(session=session, mac=mac if mac else '', **kwargs)
        new_ip_obj = self.model(ip=ip, _mac=mac_obj, domain_name=domain_name)
        net_str = str(self.___get_ip_net(ip=ip))
        if IPv4Address(ip).is_private:
            network: Network | None = session.query(Network).where(Network.network == net_str).first()
            if not network:
                gateway = self._get_ip_gateway(ip)
                db_gateway = session.query(IP).where(IP.ip == str(gateway)).first()
                if not db_gateway:
                    db_gateway = IP(ip=str(gateway), 
                                    _mac=self.mac.create(session=session, mac=mac if mac else '', **kwargs),
                                    )
                    session.add(db_gateway)
                    session.flush()
                net = Network(mask=24, network=str(self._get_ip_gateway(ip) - 1) + '/24', 
                            gateway=db_gateway, guess=True, type_id=1)
                session.add(net)
                session.flush()
                self.logger.debug(f'Created net {net}')
            else:
                db_gateway = network.gateway
            new_ip_obj.network_id = db_gateway.network_if_gateway.id
            session.flush()
        session.add(new_ip_obj)
        session.flush()
        self.logger.debug('Created "%s" with kwargs %s', self.model.__name__, {'id': getattr(new_ip_obj, 'id', 'No id'), 'ip': ip, 'mac': mac, 'domain_name': domain_name})
        return new_ip_obj
    
    @BaseQueries.session_provide
    def get_or_create(self, session: Session, ip: str, mac: str=None, 
                      domain_name: str=None,
                      to_update: bool=False, **kwargs):
        ip_obj = session.query(IP).where(IP.ip == ip).first()
        if ip_obj:
            self.logger.debug('Get "%s" with kwargs %s', self.model.__name__, {'ip': ip})
            return ip_obj
        else:
            return self.create(session=session, ip=ip, mac=mac, domain_name=domain_name, **kwargs)
        
    @BaseQueries.session_provide
    def get_by_id(self, session: Session, id: int, return_format:str = 'dict'):
        ip_obj = session.query(self.model).get(id)
        if return_format == 'dict':
            return ip_obj.to_dict()
        elif return_format == 'vis':
            return ip_obj.to_vis_node()
        else:
            return ip_obj
        
    @BaseQueries.session_provide
    def get_by_ip(self, session: Session, ip: str):
        stm = session.query(self.model).where(self.model.ip == ip)
        res: IP | None = stm.first()
        return res
    
    @BaseQueries.session_provide
    def edit_ip(self, session: Session, ip: str,
                domain: str | None,
                os: str | None,
                mac: str | None ,
                vendor: str | None
                ):
        stm = session.query(self.model).where(self.model.ip == ip)
        res: IP | None = stm.first()
        if not res:
            raise ValueError(f'No such ip({ip}) in database')
        
        res._mac.mac = mac
        res.domain_name = domain
        res._mac._obj.os = os
        res._mac.vendor = vendor
        return res
        
    @BaseQueries.session_provide
    def get_vis_nodes(self, session: Session) -> dict:
        """метод генерации ребер для построения топологии сети на веб-морде

        Args:
            session (Session): сессия коннекта к базе

        Returns:
            dict: словарь ребер
        """        
        return [nodes.to_vis_node() for nodes in session.query(self.model).all()]
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'mac', 'type': '', 'required': False},
                {'name': 'ip', 'type': '', 'required': True},
                {'name': 'domain_name', 'type': '', 'required': False},]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'mac':
            return self.mac.model.mac, self.model._mac
        
    
    
    @BaseQueries.session_provide
    def create_from_struct(self, *, session: Session, ip: IPv4Struct):
        
        ip_obj = session.query(IP).where(IP.ip == str(ip.address)).first()
        if not ip_obj:
            mac = ip.mac_address.mac if ip.mac_address else None
            ip_obj = self.create(session, ip=str(ip.address), mac=mac, domain_name=ip.domain_name)
        else:
            raise ValueError(f'IP with addr {ip.address} exist!')
        
        TO_UPDATE = ('name', 'product', 'version', 'os', 'extra_info', 'cpe')
        for port in ip.ports:
            
            db_port = session.query(Port).filter(Port.port == port.port, Port._ip == ip_obj).first()
            if not db_port:
                port_data = port.model_dump(exclude={'id'})
                service = port_data.pop('service', None)
                if service:
                    for i in TO_UPDATE:
                        port_data[i] = service.get(i)
                db_port = Port(**port_data, _ip=ip_obj)
                session.add(db_port)
                self.logger.debug(f'Created Port {db_port}')
        return ip_obj
