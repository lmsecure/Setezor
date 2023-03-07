from sqlalchemy.orm.session import Session
from database.models import ObjectType
from .base_queries import BaseQueries


class ObjectTypeQueries(BaseQueries):
    """Класс запросов к таблице типов объектов
    """    
    
    model = ObjectType
    
    def __init__(self, session_maker: Session):
        super().__init__(session_maker)
        with session_maker() as session:
            object_types = [i.object_type for i in session.query(ObjectType).all()]
            for i in ['router', 'switch', 'win_server', 'linux_server', 'firewall', 'win_pc', 
                    'linux_pc', 'nas', 'ip_phone', 'printer', 'tv', 'android_device']:  # FixMe: replace object types in file
                if i not in object_types:
                    session.add(ObjectType(object_type=i))
            session.flush()
            session.commit()
            
    def create(self, session: Session, *args, **kwargs):
        raise NotImplementedError()
    
    def get_headers(self, *args, **kwargs) -> list:
        raise NotImplementedError()