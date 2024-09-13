from typing import Any
from sqlalchemy.orm.session import Session
from sqlalchemy import func, desc
from ..models import Software, Resource_Software
from .base_queries import BaseQueries
import pandas as pd


class SoftwareQueries(BaseQueries):
    """Класс запросов к таблице портов
    """
    model = Software

    def __init__(self, session_maker: Session):
        """Метод инициализация объекта запросов

        Args:
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)


    @BaseQueries.session_provide
    def create(self, session: Session, **kwargs):
        new_soft_obj = self.model(**kwargs)
        session.add(new_soft_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, kwargs)
        return new_soft_obj


    @BaseQueries.session_provide
    def get_or_create(self, session: Session, to_update: bool = False, **kwargs):
        kwargs.pop('ip', None)
        kwargs.pop('port', None)
        obj = session.query(self.model).filter(
            *[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
        if self.check_exists(session=session, query=obj):
            if to_update:
                self.update_by_id(id=obj.first().id, to_update=kwargs)
            self.logger.debug('Get "%s" object with kwargs %s', self.model.__name__, kwargs)
            return obj.first()
        else:
            self.logger.debug('Create new "%s" object with kwargs %s', self.model.__name__, kwargs)
            return self.create(session=session, **kwargs)

    
    def get_headers(self, **kwargs) -> list:
        return [{},]
    

    @BaseQueries.session_provide
    def get_most_frequent_value_from_port(self, *, session: Session, column: str,
                                   limit: int | None = None) -> list[tuple[int|Any]]:
        """Запрос на получение самых распространенных значений в колонке.add() относительно Resource_Software
        
        Возвращает (значение, количество)
        """
        resourses = session.query(func.count(getattr(self.model, column)).label('qty'), getattr(self.model, column)).join(Resource_Software).\
                where(getattr(self.model, column) != None).group_by(getattr(self.model, column)).order_by(desc('qty')).limit(limit).all()
        return resourses



