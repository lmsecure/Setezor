from pandas.core.api import DataFrame as DataFrame
from sqlalchemy.orm.session import Session
from sqlalchemy import Column, select, func

from ..models import IP, MAC, Object, Port, Resource, Resource_Software, Software, Domain
from .base_queries import QueryFilter
from .base_queries import BaseQueries
from sqlalchemy import desc


def get_str(value):
    '''Возвращает строку, если None, то возвращает пустую строку'''

    if value:
        return str(value)
    else:
        return ''

PIVOT_COLUMNS = [
    Column(name='id'),
    Column(name='ipaddr'),
    Column(name='port'),
    Column(name='protocol'),
    Column(name='service_name'),
    Column(name='domain'),
    Column(name='vendor'),
    Column(name='product'),
    Column(name='type'),
    Column(name='version'),
    Column(name='build'),
    Column(name='patch'),
    Column(name='platform'),
    Column(name='cpe23')

]

class PivotModel:
    __name__ = 'pivot'

    @classmethod
    def get_name(cls):
        return "Resource_Software"

    def get_headers_for_table(self):
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'protocol', 'title': 'PROTOCOL'},
            {'field': 'service_name', 'title': 'SERVICE_NAME'},
            {'field': 'domain', 'title': 'DOMAIN'},
            {'field': 'vendor', 'title': 'VENDOR'},
            {'field': 'type', 'title': 'TYPE'},
            {'field': 'product', 'title': 'PRODUCT'},
            {'field': 'version', 'title': 'VERSION'},
            {'field': 'build', 'title': 'BUILD'},
            {'field': 'patch', 'title': 'PATCH'},
            {'field': 'platform', 'title': 'PLATFORM'},
            {'field': 'cpe23', 'title': 'CPE23'},
        ]


class PivotResourceSoftwareQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """

    model = PivotModel()

    def __init__(self, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)

    @BaseQueries.session_provide
    def get_info_about_node(self, session: Session, ip_id: int):
        """Составление дикта для информации о ноде"""

        query = session.query(IP).where(IP.id == ip_id)
        res: IP | None = query.first()
        result = {}
        if res:
            ip: str = res.ip
            if ip:
                result['ip'] = ip
            mac: MAC = res._mac
            mac_str = mac.mac
            if mac_str:
                result['mac'] = mac_str
            domain = res.domain_name
            if domain:
                result['domain'] = domain
            vendor = mac.vendor
            if vendor:
                result['vendor'] = vendor
            obj: Object = mac._obj
            os = obj.os
            if os:
                result['os'] = os
            resourses = session.query(Port, Resource, Resource_Software, Software).\
                where(Port.id == Resource.port_id).\
                where(Resource.id == Resource_Software.resource_id).\
                where(Resource_Software.software_id == Software.id).\
                where(Resource.ip_id == res.id).all()
            ports = []
            for resourse in resourses:
                port = {}
                port.update({'number': get_str(resourse.Port.port), 'protocol': get_str(resourse.Port.protocol),
                             'name': resourse.Port.service_name, 'product': get_str(resourse.Software.product)})
                ports.append(port)
            if ports:
                result['ports'] = ports
        return result

    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, obj=None, **kwargs):
        raise NotImplementedError()

    @BaseQueries.session_provide
    def get_records_count(self, session: Session):
        return session.query(func.count(IP.ip)).scalar()

    def get_headers(self) -> list:
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'protocol', 'title': 'PROTOCOL'},
            {'field': 'service_name', 'title': 'SERVICE_NAME'},
            {'field': 'domain', 'title': 'DOMAIN'},
            {'field': 'vendor', 'title': 'VENDOR'},
            {'field': 'type', 'title': 'TYPE'},
            {'field': 'product', 'title': 'PRODUCT'},
            {'field': 'version', 'title': 'VERSION'},
            {'field': 'build', 'title': 'BUILD'},
            {'field': 'patch', 'title': 'PATCH'},
            {'field': 'platform', 'title': 'PLATFORM'},
            {'field': 'cpe23', 'title': 'CPE23'},
        ]

    @BaseQueries.session_provide
    def get_all(self, session: Session, result_format: str = None,
                page: int = None, limit: int = None, sort_by: str = None,
                direction: str = None, filters: list[QueryFilter] = []) -> list[dict] | DataFrame:

        query = session.query(
            func.row_number().over().label('id'),
            IP.ip.label("ipaddr"),
            Port.port.label("port"),
            Port.protocol.label("protocol"),
            Port.service_name.label("service_name"),
            Domain.domain.label("domain"),
            Software.vendor.label("vendor"),
            Software.product.label("product"),
            Software.type.label("type"),
            Software.version.label("version"),
            Software.build.label("build"),
            Software.patch.label("patch"),
            Software.platform.label("platform"),
            Software.cpe23.label("cpe23"),
            Resource,
        ).join(Resource_Software, Resource.id == Resource_Software.resource_id
               ).join(Software, Resource_Software.software_id == Software.id
                      ).join(IP, Resource.ip_id == IP.id, isouter=True
                             ).join(Port, Resource.port_id == Port.id, isouter=True
                                    ).join(Domain, Resource.domain_id == Domain.id, isouter=True)

        res = self._get_all(session=session, source_query=query,
                            columns=PIVOT_COLUMNS,
                            result_format=result_format, page=page,
                            limit=limit, sort_by=sort_by, direction=direction,
                            filters=filters, model=self.model)
        result = []
        for i in res:
            record = {
                'id': i[0],
                'ipaddr': i[1],
                'port': i[2],
                'protocol': i[3],
                'service_name': i[4],
                'domain': i[5],
                'vendor': i[6],
                'product': i[7],
                'type': i[8],
                'version': i[9],
                'build': i[10],
                'patch': i[11],
                'platform': i[12],
                'cpe23': i[13]
            }
            result.append(record)
        return result
