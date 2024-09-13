from .base_queries import BaseQueries
from ..models import Resource_Software
from .resource_queries import ResourceQueries
from .software_queries import SoftwareQueries
from sqlalchemy.orm.session import Session

from setezor.network_structures import SoftwareStruct


class ResourceSoftwareQueries(BaseQueries):
    model = Resource_Software

    def __init__(self, resource: ResourceQueries, software: SoftwareQueries, session_maker: Session):
        """Метод инициализация объекта запросов

        Args:
            resourse (ResourceQueries): объект запросов к таблице ResourceSoftware
            software (SoftwareQueries): объект запросов к таблице Software
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)
        self.resource = resource
        self.software = software

    @BaseQueries.session_provide
    def write_many(self, session: Session, data: list, to_update: bool = True):
        """Делает множественную запись объектов по такому же принципу
        Если объект несуществует - записываем, если существует - не делаем ничего

        Args:
            session (Session): сессия коннекта к базе
            data (list): массив данных
        """
        objects = (self.get_or_create(session=session,
                   to_update=to_update, **item) for item in data)
        objects = [i for i in objects if i]
        self.logger.info('Add %s "%s"', len(objects), self.model.__name__)
        session.flush()

    @BaseQueries.session_provide
    def create(self, session: Session, **kwargs):
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
        self.logger.debug('Created "%s" object with kwargs %s',
                          self.model.__name__, kwargs)
        return new_vuln_res_soft

    @BaseQueries.session_provide
    def get_or_create(self, session: Session, to_update: bool = False, **kwargs):
        resource = {'port': kwargs.get('port')}
        if 'ip' in kwargs:
            resource.update({'ip': kwargs.get('ip')})
        if 'domain' in kwargs:
            resource.update({'domain': kwargs.get('domain')})
        obj_resource = self.resource.get_or_create(session=session, **resource)
        soft = SoftwareStruct(**kwargs)
        obj_software = self.software.get_or_create(
            session=session, **soft.model_dump())
        resource_soft = {'resource_id': obj_resource.id,
                         'software_id': obj_software.id}
        obj = session.query(self.model).filter(
            *[self.model.__table__.c.get(k) == v for k, v in resource_soft.items() if v])

        if self.check_exists(session=session, query=obj):
            if to_update:
                self.update_by_id(id=obj.first().id, to_update=kwargs)
            self.logger.debug('Get %s object with kargs %s',
                              self.model.__name__, kwargs)
            return obj.first()
        else:
            self.logger.debug(
                'Create new "%s" object with kwargs %s', self.model.__name__, kwargs)
            return self.create(session=session, **resource_soft)

    @BaseQueries.session_provide
    def get_or_create_by_ids(self, session: Session, to_update: bool = False, **kwargs):
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
