from pandas import DataFrame
from sqlalchemy import func
from .base_queries import BaseQueries, QueryFilter
from .ip_queries import IPQueries
from .domain_queries import DomainQueries
from .port_queries import PortQueries
from setezor.database.models import Resource_Software_Vulnerability_Screenshot
from sqlalchemy.orm.session import Session


class ResourceSoftwareVulnerabilityScreenshotQueries(BaseQueries):
    model = Resource_Software_Vulnerability_Screenshot

    def __init__(self,session_maker: Session):
        """Метод инициализации объекта запросов

        Args:
            ip (IPQueries): объект запросов к таблице с ip адресами
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)
        
    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, obj=None, **kwargs):
        raise NotImplementedError()


    def get_headers(self) -> list:
        return []