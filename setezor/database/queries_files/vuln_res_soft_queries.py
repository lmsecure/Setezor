from .base_queries import BaseQueries
from ..models import Vulnerability_Resource_Soft
from sqlalchemy.orm.session import Session


class VulnerabilityResSoftQueries(BaseQueries):
    model = Vulnerability_Resource_Soft


    @BaseQueries.session_provide   
    def write_many(self, session: Session,data: list, to_update: bool = True):
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
    def create(self, session: Session,**kwargs):
        """Метод создания объекта домена

        Args:
            session (Session): сессия коннекта к базе
            domain (str): доменное имя

        Returns:
            _type_: объект доменного имени
        """
        new_vuln_res_soft = self.model(**kwargs)
        session.add(new_vuln_res_soft)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, kwargs)
        return new_vuln_res_soft


    @BaseQueries.session_provide
    def get_or_create(self, session: Session, to_update: bool = False, **kwargs):
        obj = session.query(self.model).filter(
            *[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
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

    def get_headers(self) -> list:
            return [{},]