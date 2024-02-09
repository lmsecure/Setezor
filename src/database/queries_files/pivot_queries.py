from pandas.core.api import DataFrame as DataFrame
from sqlalchemy.orm.session import Session

from database.models import Pivot, IP, MAC, Object, Port
from database.queries_files.base_queries import QueryFilter
from .base_queries import BaseQueries
from .object_queries import ObjectQueries

def get_str(value):
    
    '''Возвращает строку, если None, то возвращает пустую строку'''
    
    if value:
        return str(value)
    else:
        return ''

class PivotQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """    
    
    model = Pivot
    
    def __init__(self, objects: ObjectQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.object = objects
    
    @BaseQueries.session_provide
    def get_info_about_node(self, session: Session, ip_id: int):
        
        """Составление дикта для информации о ноде"""
        
        query = session.query(IP).where(IP.id == ip_id)
        res: IP | None = query.first()
        result = {}
        if res:
            ip: str = res.ip
            if ip:
                result['ip'] = ip
            mac: MAC = res._mac
            mac_str = mac.mac
            if mac_str:
                result['mac'] = mac_str
            domain = res.domain_name
            if domain:
                result['domain'] = domain
            vendor = mac.vendor
            if vendor:
                result['vendor'] = vendor
            obj: Object = mac._obj
            os = obj.os
            if os:
                result['os'] = os
            ports = session.query(Port).where(Port.ip == res.id).all()
            ports = [{'number': get_str(i.port), 'protocol': get_str(i.protocol), 'name': get_str(i.service_name), 'product': get_str(i.product)} for i in ports]
            if ports:
                result['ports'] = ports

        return result
        
    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, obj=None, **kwargs):
        raise NotImplementedError()   

    def get_headers(self) -> list:
        return  Pivot.get_headers_for_table()
    