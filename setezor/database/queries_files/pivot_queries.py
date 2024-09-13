from pandas.core.api import DataFrame as DataFrame
from sqlalchemy.orm.session import Session
from sqlalchemy import Column, select, func

from ..models import IP, MAC, Object, Port, Resource, Resource_Software, Software
from ..queries_files.base_queries import QueryFilter
from .base_queries import BaseQueries

def get_str(value):
    
    '''Возвращает строку, если None, то возвращает пустую строку'''
    
    if value:
        return str(value)
    else:
        return ''

PIVOT_COLUMNS = [
    Column(name='id'),
    Column(name='ip'),
    Column(name='port'),
    Column(name='mac')
]

class PivotModel:
    
    __name__ = 'pivot'
    
    
    def get_headers_for_table(self):
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ip', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'mac', 'title': 'MAC'}
            ]


class PivotQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """ 
    
    model = PivotModel() 

    def __init__(self, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
    
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
            resourses = session.query(Port, Resource, Resource_Software, Software).\
            where(Port.id == Resource.port_id).\
            where(Resource.id == Resource_Software.resource_id).\
            where(Resource_Software.software_id == Software.id).\
            where(Resource.ip_id == res.id).all()
            ports = []
            for resourse in resourses:
                port = {}
                port.update({'number' : get_str(resourse.Port.port), 'protocol' : get_str(resourse.Port.protocol), 
                             'name' : resourse.Port.service_name, 'product' : get_str(resourse.Software.product)})
                ports.append(port)
            if ports:
                result['ports'] = ports
        return result
        
    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, obj=None, **kwargs):
        raise NotImplementedError()
    
    @BaseQueries.session_provide
    def get_records_count(self, session: Session):
        return session.query(func.count(IP.ip)).scalar()
        

    def get_headers(self) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ip', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'mac', 'title': 'MAC'}
            ]
    
    @BaseQueries.session_provide
    def get_all(self, session: Session, result_format: str = None, 
                page: int = None, limit: int = None, sort_by: str = None, 
                direction: str = None, filters: list[QueryFilter] = ...) -> list[dict] | DataFrame:
        
        query = session.query(
            func.row_number().over().label('id'),
            IP.ip,
            Port.port,
            MAC.mac
                          ).join(
                              MAC, MAC.id == IP.mac, isouter=True
                              ).join(
                                  Port, Port.ip == IP.id, isouter=True
                              )
        res = self._get_all(session=session, source_query=query, 
                              columns=PIVOT_COLUMNS,
                              result_format=result_format, page=page,
                              limit=limit, sort_by=sort_by, direction=direction,
                              filters=filters, model=self.model)
        res = [
            {'id': i[0], 'ip': i[1], 'port': i[2], 'mac': i[3]} for i in res
        ]
        return res