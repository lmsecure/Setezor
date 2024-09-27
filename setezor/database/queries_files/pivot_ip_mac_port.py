from pandas.core.api import DataFrame as DataFrame
from sqlalchemy.orm.session import Session
from sqlalchemy import Column, select, func

from ..models import IP, MAC, Port
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
    Column(name='mac'),
]

class PivotIPMacPortModel:
    __name__ = 'pivot_ip_mac_port'

    @classmethod
    def get_name(cls):
        return "IP_MAC_PORT"

    def get_headers_for_table(self):
        return [
            {'field': 'id', 'title': 'ID'},
            {'field': 'ipaddr', 'title': 'IP'},
            {'field': 'port', 'title': 'PORT'},
            {'field': 'mac', 'title': 'MAC'},
        ]


class PivotIpMacPortQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """

    model = PivotIPMacPortModel()

    def __init__(self, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """
        super().__init__(session_maker)


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
            {'field': 'mac', 'title': 'MAC'},
        ]

    @BaseQueries.session_provide
    def get_all(self, session: Session, result_format: str = None,
                page: int = None, limit: int = None, sort_by: str = None,
                direction: str = None, filters: list[QueryFilter] = []) -> list[dict] | DataFrame:

        query = session.query(
            func.row_number().over().label('id'),
            IP.ip.label("ipaddr"),
            Port.port.label("port"),
            MAC.mac.label("mac"),
            IP).join(IP, IP.mac == MAC.id).join(Port, Port.ip == IP.id, isouter=True)

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
                'mac':i[3]
            }
            result.append(record)
        return result
