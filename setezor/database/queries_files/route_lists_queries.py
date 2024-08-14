from sqlalchemy.orm.session import Session
from ..models import RouteList
from .base_queries import BaseQueries


class RouteListQueries(BaseQueries):
    """Класс запросов к таблице скриншотов
    """
    model = RouteList
    
    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)
    
    def create(self, session: Session, *args, **kwargs):
        return super().create(session, *args, **kwargs)
    