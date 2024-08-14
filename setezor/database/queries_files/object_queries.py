from sqlalchemy.orm.session import Session
from ..models import Object, IP
from .base_queries import BaseQueries


class ObjectQueries(BaseQueries):
    """Класс запросов к таблице объектов
    """    
    
    model = Object
    
    @BaseQueries.session_provide
    def create(self, session: Session, obj_type: str = None, os: str = None, 
               status: str = None, **kwargs):
        """Метод создания объекта

        Args:
            session (Session): сессия коннекта к базе
            obj_type (str): тип объекта
            os (str): сведения об ОС
            status (str): статус

        Returns:
            _type_: объект из таблицы объектов
        """        
        new_obj_obj = Object(object_type=obj_type, os=os, status=status)
        session.add(new_obj_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'object_type': obj_type, 'os': os, 'status': status})
        obj_obj = new_obj_obj
        return obj_obj
    
    @BaseQueries.session_provide
    def update_by_ip_id(self, session: Session, ip_id: int, to_update: dict):
        ip = session.query(IP).get(ip_id)
        if ip:
            obj = session.query(self.model).filter(self.model.id == ip._mac._obj.id).update(to_update)
            session.flush()
            
    @BaseQueries.session_provide
    def add_os(self, session: Session, obj: Object, os: str):
        session.add(obj)
        obj.os = os
            
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'object_type', 'type': '', 'required': True},
                {'name': 'os', 'type': '', 'required': True},
                {'name': 'status', 'type': '', 'required': True},]