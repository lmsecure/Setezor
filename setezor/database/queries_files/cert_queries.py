import sys
from sqlalchemy.orm.session import Session
from setezor.database.models import Cert, Domain, IP
from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from sqlalchemy import JSON, DATETIME, BOOLEAN
from ..queries_files.domain_queries import DomainQueries
from ..queries_files.ip_queries import IPQueries


class CertQueries(BaseQueries):
    """Класс запросов к таблице DNS
    """

    model = Cert

    def __init__(self, domain: DomainQueries, ip: IPQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)
        self.domain = domain
        self.ip = ip

    @BaseQueries.session_provide
    def get_obj(self, session: Session, cert: Cert):
        session.add(cert)
        return cert._obj

    @BaseQueries.session_provide
    def create(self, session: Session, **kwargs):
        """Метод создания объекта домена

        Args:
            session (Session): сессия коннекта к базе
            domain (str): доменное имя

        Returns:
            _type_: объект доменного имени
        """
        new_cert_obj = self.model(**kwargs)
        session.add(new_cert_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s',
                          self.model.__name__, {'data': kwargs})
        cert_obj = new_cert_obj
        return cert_obj

    @BaseQueries.session_provide
    def get_or_create(self, session: Session, to_update: bool = False, **kwargs):
        """Получает объект из базы, если его не существует - создает

        Args:
            session (_type_): сессия коннекта к базе

        Returns:
            _type_: объект записи из базы
        """
        
        if kwargs.get("domain"):
            target = kwargs.pop("domain")
            db_domain = self.domain.get_or_create(domain=target)
            kwargs["domain_id"] = db_domain.id
            kwargs["ip_id"] = db_domain.ip_id
        if kwargs.get("ip"):
            target = kwargs.pop("ip")
            db_ip = self.ip.get_or_create(ip = target)
            kwargs["ip_id"] = db_ip.id
        obj = session.query(self.model).filter(*[self.model.__table__.c.get(k) == v for k, v in kwargs.items() if v])
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

    def foreign_key_order(self, field_name: str):
        if field_name == 'object':
            return self.object.model.object_type, self.model._obj

    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},]
