from sqlalchemy.orm.session import Session
from ..models import Port
from .base_queries import BaseQueries
from .ip_queries import  IPQueries
import pandas as pd


class PortQueries(BaseQueries):
    """Класс запросов к таблице портов
    """    
    model = Port
    
    def __init__(self, ip: IPQueries, session_maker: Session):
        """Метод инициализации объекта запросов

        Args:
            ip (IPQueries): объект запросов к таблице с ip адресами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.ip = ip
        
    @BaseQueries.session_provide
    def create(self, session: Session, ip: str, port: int, protocol: str=None, mac: str=None, state: str=None, service_name: str=None, **kwargs):
        """Метод создания объекта порта

        Args:
            session (Session): сессия коннекта к базе
            ip (str): ip адрес
            port (int): порт
            mac (str, optional): mac адрес. Defaults to None.
            service_name (str, optional): название сервиса. Defaults to None.
            protocol
            state (str, optional): состояние. Defaults to None.

        Returns:
            _type_: объект порта
        """
        if ip:
            ip_obj = self.ip.get_or_create(session=session, ip=ip)
        else:
            ip_obj = self.ip.create(session=session, ip='', **kwargs)
        new_port_obj = self.model(ip=ip_obj.id, protocol=protocol, port=int(port), service_name=service_name, state=state)
        session.add(new_port_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'ip': ip, 'port': port, 'mac': mac, 'state': state, 'service_name' : service_name})
        port_obj = new_port_obj
        return port_obj
    
    @BaseQueries.session_provide
    def get_or_create(self, session: Session, ip: str, port: int, protocol: str=None, mac: str=None,
                      service_name: str=None, state: str=None, to_update: bool=False, **kwargs):
        ip_obj = self.ip.get_or_create(session=session, ip=ip, mac=mac, **kwargs)
        port_query = session.query(self.model).filter(self.model.__table__.c.get('ip') == ip_obj.id, self.model.__table__.c.get('port') == port)
        if self.check_exists(session=session, query=port_query):
            if to_update:
                self.update_by_id(id=port_query.first().id, to_update=dict(ip=ip, port=port, protocol=protocol, mac=mac, service_name=service_name, state=state))
            return port_query.first()
        else:
            return self.create(session=session, ip=ip, port=port, protocol=protocol, mac=mac, service_name=service_name, state=state)
    

    @BaseQueries.session_provide
    def get_or_create_by_ipid(self, session: Session, ip_id: int, port : int, protocol: str=None, mac: str=None,
                      service_name: str=None, state: str=None, to_update: bool=False, **kwargs):
        ip = self.ip.get_by_id(id= ip_id).get("ip")
        port_query = session.query(self.model).filter(self.model.__table__.c.get('ip') == ip_id, self.model.__table__.c.get('port') == port)
        if self.check_exists(session=session, query=port_query):
            if to_update:
                self.update_by_id(id=port_query.first().id, to_update=dict(ip=ip, port=port, protocol=protocol, mac=mac, service_name=service_name, state=state))
            return port_query.first()
        else:
            return self.create(session=session, ip=ip, port=port, protocol=protocol, mac=mac, service_name=service_name, state=state)


    @BaseQueries.session_provide
    def get_ports_by_ip(self, session: Session, ip_ids: list) -> dict:
        """Метод получения всех портов по идентификатору ip адреса

        Args:
            session (Session): сессия коннекта к базе
            ip_id (int): идентификатор ip адреса

        Returns:
            dict: словарь заголовков таблицы и сведений о портах
        """
        ports_data = []
        for i in ip_ids:
            s = [i.to_dict() for i in session.query(self.model).filter(self.model.ip == i).all()]
            ports_data += s
        df = pd.DataFrame(ports_data).fillna('')
        return df.to_dict('records')
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'ip', 'type': '', 'required': True},
                {'name': 'port', 'type': '', 'required': True},
                {'name': 'protocol', 'type': '', 'required': False},
                {'name': 'service_name', 'type': '', 'required': False},
                {'name': 'state', 'type': '', 'required': False}]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'ip':
            return self.ip.model.ip, self.model._ip