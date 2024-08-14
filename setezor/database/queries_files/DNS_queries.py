import asyncio
import sys
from sqlalchemy.orm.session import Session
from setezor.database.models import DNS, Domain
from setezor.tasks.domain_task import SdFindTask
from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from ..queries_files.domain_queries import DomainQueries



class DNSQueries(BaseQueries):
    """Класс запросов к таблице DNS
    """    
    
    model = DNS
    
    def __init__(self, domain: DomainQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.domain = domain
    
    
    @BaseQueries.session_provide
    def get_obj(self, session: Session, dns: DNS):
        session.add(dns)
        return dns._obj
        
    @BaseQueries.session_provide
    def create(self, session: Session, domain_id: int, record_type: str,record_value:str, obj=None, **kwargs):
        """Метод создания объекта домена

        Args:
            session (Session): сессия коннекта к базе
            domain (str): доменное имя

        Returns:
            _type_: объект доменного имени
        """
        new_dns_obj = self.model(record_value=record_value, record_type=record_type,domain_id=domain_id)
        session.add(new_dns_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'dns': "db is uptade"})
        dns_obj = new_dns_obj
        return dns_obj
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'object':
            return self.object.model.object_type, self.model._obj

    @BaseQueries.session_provide   
    def write_many(self, session: Session,domain:str, data: list, to_update: bool = True):
        """Делает множественную запись объектов по такому же принципу
        Если объект несуществует - записываем, если существует - не делаем ничего

        Args:
            session (Session): сессия коннекта к базе
            data (list): массив данных
        """
        objects = (self.get_or_create(session=session, to_update=to_update,domain = domain, **item) for item in data)
        objects = [i for i in objects if i]
        self.logger.info('Add %s "%s"', len(objects), self.model.__name__)
        session.flush()


    @BaseQueries.session_provide    
    def get_or_create(self, session: Session, domain: str,to_update: bool = False, **kwargs):
        db_domain=self.domain.get_or_create(session=session, domain=domain)
        kwargs.update({
            "domain_id" : db_domain.id
        })
        obj = session.query(self.model).filter(*[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
        if self.check_exists(session=session, query=obj):
            if to_update:
                self.update_by_id(id=obj.first().id, to_update=kwargs)
            self.logger.debug('Get "%s" object with kwargs %s',
                              self.model.__name__, kwargs)
            return obj.first()
        else:
            self.logger.debug(
                'Create new "%s" object with kwargs %s', self.model.__name__, kwargs)
            return self.create(session=session, **kwargs)