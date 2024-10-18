from .base_queries import BaseQueries
from ..models import Vulnerability_Resource_Soft
from sqlalchemy.orm.session import Session
from ..models import Resource_Software_Vulnerability_Screenshot

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

    @BaseQueries.session_provide
    def set_confirm(self, session: Session, id:int,status:bool):
        obj = session.query(self.model).get(id)
        obj.confirmed = status
        session.flush()

    @BaseQueries.session_provide
    def save_screenshot(self, session: Session,**kwargs):
        new_screenshot = Resource_Software_Vulnerability_Screenshot(
            resource_vulnerability_id = kwargs.get("resource_vuln_id"),
            note = kwargs.get("note"),
            path = kwargs.get("path")
        )
        session.add(new_screenshot)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', Resource_Software_Vulnerability_Screenshot.__name__, kwargs)
        return new_screenshot
    
    @BaseQueries.session_provide
    def get_screenshots(self, session: Session,**kwargs):
        id = kwargs.get("resource_vuln_id")
        screenshots = session.query(Resource_Software_Vulnerability_Screenshot)\
            .filter(Resource_Software_Vulnerability_Screenshot.resource_vulnerability_id == id).all()
        self.logger.debug('Get "%s" objects with kwargs %s',Resource_Software_Vulnerability_Screenshot.__name__, kwargs)
        return screenshots

    
    
    
    def get_headers(self) -> list:
            return [{},]