from sqlalchemy.orm.session import Session
from database.models import IP
from database.queries_files.base_queries import Mock, BaseQueries
from database.queries_files.mac_queries import MACQueries


class IPQueries(BaseQueries):
    """Класс запросов к таблице IP адресов
    """    
    
    model = IP
    
    def __init__(self, mac: MACQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            mac (MACQueries): объект запросов к таблице с mac адресами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.mac = mac
        
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
        # if mac:
        #     mac_obj = self.mac.get_or_create(session=session, mac=mac)
        # else:
        mac_obj = self.mac.create(session=session, mac=mac if mac else '', **kwargs)
        new_ip_obj = self.model(ip=ip, _mac=mac_obj, domain_name=domain_name)
        session.add(new_ip_obj)
        session.flush()
        self.logger.debug('Created "%s" with kwargs %s', self.model.__name__, {'ip': ip, 'mac': mac, 'domain_name': domain_name})
        return new_ip_obj
    
    @BaseQueries.session_provide
    def get_or_create(self, session: Session, ip: str, mac: str=None, domain_name: str=None, to_update: bool=False, **kwargs):
        ip_obj = session.query(self.model).filter(self.model.__table__.c.get('ip') == ip).first()
        if ip_obj:
            self.logger.debug('Get "%s" with kwargs %s', self.model.__name__, {'ip': ip})
            return ip_obj
        else:
            return self.create(session=session, ip=ip, mac=mac, domain_name=domain_name)
        
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