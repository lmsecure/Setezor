import sys
from sqlalchemy.orm.session import Session
from setezor.database.models import Domain
from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from sqlalchemy import BOOLEAN
from ..queries_files.ip_queries import IPQueries
from setezor.tasks.domain_task import SdFindTask
import asyncio
from setezor.tools import ip_tools

class DomainQueries(BaseQueries):
    """Класс запросов к таблице доменов
    """    
    
    model = Domain
    
    def __init__(self, ip:IPQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.ip = ip
    
    
    @BaseQueries.session_provide
    def get_obj(self, session: Session, domain: Domain):
        session.add(domain)
        return domain._obj
        
    @BaseQueries.session_provide
    def create(self, session: Session, domain: str,is_wildcard:BOOLEAN, obj=None, ip_id:int=None, **kwargs):
        """Метод создания объекта домена

        Args:
            session (Session): сессия коннекта к базе
            domain (str): доменное имя

        Returns:
            _type_: объект доменного имени
        """
        new_domain_obj = self.model(domain=domain,ip_id=ip_id, is_wildcard = is_wildcard)
        session.add(new_domain_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'domain': domain})
        domain_obj = new_domain_obj
        return domain_obj
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'domain', 'type': '', 'required': False},]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'object':
            return self.object.model.object_type, self.model._obj
        
        
    @BaseQueries.session_provide   
    def write_many(self, session: Session, data: list, to_update: bool=True):
        """Делает множественную запись объектов по такому же принципу
        Если объект несуществует - записываем, если существует - не делаем ничего

        Args:
            session (Session): сессия коннекта к базе
            data (list): массив данных
        """
        objects = (self.get_or_create(session=session, to_update=to_update, **item) for item in data)
        objects = [i for i in objects if i]
        self.logger.info('Add %s "%s"', len(objects), self.model.__name__)
        session.flush()


    @BaseQueries.session_provide    
    def get_or_create(self, session: Session, domain: str,is_wildcard:bool = None, obj=None, **kwargs):
        db_domain = session.query(Domain).where(Domain.domain==domain).first()
        if not db_domain:
            ip_from_task = asyncio.run(ip_tools.get_ip_by_domain_name(domain))
            if ip_from_task:
                ip_db = self.ip.get_or_create(session = session, ip = ip_from_task,domain_name = domain)
                kwargs.update({"ip_id":ip_db.id})
            db_domain=self.create(session=session, domain=domain,is_wildcard=is_wildcard, obj=obj, **kwargs)
        return db_domain

