from sqlalchemy.orm.session import Session
from ..models import IP, MAC, Object, Port
from ..queries_files.base_queries import Mock, BaseQueries
from ..queries_files.mac_queries import MACQueries
from ..queries_files.network_queries import NetworkQueries

import ipaddress

try:
    from network_structures import IPv4Struct, IPv6Struct
except ImportError:
    from ...network_structures import IPv4Struct, IPv6Struct

class IPQueries(BaseQueries):
    """Класс запросов к таблице IP адресов
    """    
    
    model = IP
    
    def __init__(self, mac: MACQueries, network: NetworkQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            mac (MACQueries): объект запросов к таблице с mac адресами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.mac = mac
        self.network = network
        
    @BaseQueries.session_provide
    def create(self, session: Session, ip: str, mac: str=None, domain_name: str=None, **kwargs):
        """Метод создания объекта IP адреса

        Args:
            session (Session): сессия коннекта к базе
            ip (str): ip адрес
            mac (str, optional): mac адрес. Defaults to None.
            domain_name (str, optional): доменное имя. Defaults to None.

        Returns:
            _type_: объект ip адреса
        """
        if not mac:
            mac_obj = self.mac.create(session=session, mac=None, **kwargs)
        else:
            mac_obj = self.mac.get_or_create(session=session, mac=mac, **kwargs)
        # mac_obj = self.mac.get_or_create(session=session, mac=mac if mac else '', **kwargs)

        network_obj = self.network.get_or_create(session=session, ip=ip, mask=kwargs.get("mask", 24), type_id = kwargs.get("type_id", 2))

        new_ip_obj = self.model(ip=ip, _mac=mac_obj, domain_name=domain_name, network_id=network_obj.id) #domain_name=domain_name 
        session.add(new_ip_obj)
        session.flush()
        self.logger.debug('Created "%s" with kwargs %s', self.model.__name__, {'ip': ip, 'mac': mac,'domain_name': domain_name}) #'domain_name': domain_name
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
    def update_by_id(self, session: Session, *, id: int, to_update: dict, merge_mode='merge'):
        obj_ip = session.query(self.model).filter(self.model.id == id)
        obj_ip.update(to_update)
        session.flush()

        
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
                ]
        
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
