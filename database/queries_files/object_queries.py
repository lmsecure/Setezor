from sqlalchemy.orm.session import Session
from database.models import Object
from database.queries_files.base_queries import BaseQueries


class ObjectQueries(BaseQueries):
    """Класс запросов к таблице объектов
    """    
    
    model = Object
    
    @BaseQueries.session_provide
    def create(self, session: Session, obj_type: str, os: str, status: str, **kwargs):
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