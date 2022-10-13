from sqlalchemy.orm.session import Session
from database.models import MAC
from database.queries_files.base_queries import BaseQueries
from database.queries_files.object_queries import ObjectQueries


class MACQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """    
    
    model = MAC
    
    def __init__(self, objects: ObjectQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.object = objects
        
    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, **kwargs):
        """Метод создания объекта mac адреса

        Args:
            session (Session): сессия коннекта к базе
            mac (str): mac адрес

        Returns:
            _type_: объект mac адреса
        """        
        new_mac_obj = self.model(mac=mac)
        session.add(new_mac_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'mac': mac})
        mac_obj = new_mac_obj
        return mac_obj