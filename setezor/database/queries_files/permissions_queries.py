from sqlalchemy.orm.session import Session
from ..models import Permissions
from .base_queries import BaseQueries


class PermissionsQueries(BaseQueries):
    """Класс запросов к таблице типов объектов
    """    
    
    model = Permissions
    
    def __init__(self, session_maker: Session):
        super().__init__(session_maker)
        with session_maker() as session:
            permission = [item.permission for item in session.query(Permissions).all()]
            for id, p in {1:'read', 2:'write', 4:'execute'}.items():
                if p not in permission:
                    session.add(Permissions(id=id, permission=p))
            session.flush()
            session.commit()
            
    def create(self, session: Session, *args, **kwargs):
        raise NotImplementedError()
    
    def get_headers(self, *args, **kwargs) -> list:
        raise NotImplementedError()