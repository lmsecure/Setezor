from pandas import DataFrame
from sqlalchemy import func
from .base_queries import BaseQueries, QueryFilter
from .ip_queries import IPQueries
from .domain_queries import DomainQueries
from .port_queries import PortQueries
from setezor.database.models import Resource, IP, Port, Domain, Resource_Software, Vulnerability_Resource_Soft
from sqlalchemy.orm.session import Session


class ResourceQueries(BaseQueries):
    model = Resource

    def __init__(self, ip: IPQueries, domain: DomainQueries, port: PortQueries, session_maker: Session):
        """Метод инициализации объекта запросов

        Args:
            ip (IPQueries): объект запросов к таблице с ip адресами
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)
        self.ip = ip
        self.domain = domain
        self.port = port

    @BaseQueries.session_provide
    def create(self, session: Session,**kwargs):
        new_resource_obj = self.model(**kwargs)
        session.add(new_resource_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s',
                          self.model.__name__, {'data': kwargs})
        return new_resource_obj

    @BaseQueries.session_provide
    def get_or_create(self, session: Session,
                      to_update: bool = False,
                      **kwargs):
        if kwargs.get("domain"):
            target = kwargs.pop("domain")
            db_domain = self.domain.get_or_create(domain=target)
            kwargs["domain_id"] = db_domain.id
            if db_domain.ip_id:
                kwargs["ip_id"] = db_domain.ip_id
                ip_addr = self.ip.get_by_id(id=db_domain.ip_id)
                if kwargs.get("port"):
                    port = kwargs.pop("port")
                    db_port = self.port.get_or_create(port=port, ip=ip_addr["ip"])
                    kwargs["port_id"] = db_port.id
        if kwargs.get("ip"):
            target = kwargs.pop("ip")
            db_ip = self.ip.get_or_create(ip=target)
            kwargs["ip_id"] = db_ip.id
            if kwargs.get("port"):
                port = kwargs.pop("port")
                db_port = self.port.get_or_create(port=port, ip=target)
                kwargs["port_id"] = db_port.id
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
    def get_by_acunetix_id(self,session:Session,id:str):
        return session.query(self.model).filter(self.model.acunetix_id == id).first()
    
    def get_headers(self) -> list:
            return [{'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'domain', 'title': 'DOMAIN'},
            {'field': 'vuln_count', 'title': 'VulnCount'},
            ]
    

    @BaseQueries.session_provide
    def get_all(self, session: Session, result_format: str = None,
                page: int = None, limit: int = None, sort_by: str = None,
                direction: str = None, filters: list[QueryFilter] = []) -> list[dict] | DataFrame:

        query = session.query(
            Resource.id,
            IP.ip.label("ipaddr"),
            Port.port.label("port"),
            Domain.domain.label("domain"),
            func.count(Vulnerability_Resource_Soft.vulnerability_id).label("cnt")).select_from(Resource)\
            .join(IP, Resource.ip_id == IP.id, isouter=True)\
            .join(Port, Resource.port_id == Port.id, isouter=True)\
            .join(Domain, Resource.domain_id == Domain.id, isouter=True)\
            .join(Resource_Software, Resource_Software.resource_id == Resource.id)\
            .join(Vulnerability_Resource_Soft, Resource_Software.id == Vulnerability_Resource_Soft.resource_soft_id, isouter=True)\
            .group_by(Resource.id,"ipaddr","port","domain")

        res = self._get_all(session=session, source_query=query,
                            columns=[],
                            result_format=result_format, page=page,
                            limit=limit, sort_by=sort_by, direction=direction,
                            filters=filters, model=self.model)
        result = []
        for i in res:
            record = {
                'id': i[0],
                'ipaddr': i[1],
                'port': i[2],
                'domain': i[3],
                "vuln_count":i[4],
            }
            result.append(record)
        return result