from typing import TYPE_CHECKING

from pandas.core.api import DataFrame as DataFrame
from sqlalchemy.orm.session import Session

import orjson

if TYPE_CHECKING:
    from database.queries_files.base_queries import QueryFilter
from ..models import Agent, Object, IP, MAC
from ..queries_files.base_queries import BaseQueries
from .ip_queries import IPQueries
from .route_queries import RouteQueries

try:
    from network_structures import AgentStruct, IPv4Struct, RouteStruct
except ImportError:
    from ...network_structures import AgentStruct, IPv4Struct, RouteStruct


class AgentQueries(BaseQueries):
    """Класс запросов к таблице агентов"""

    model = Agent
    
    def __init__(self, session_maker: Session, ip_queries: IPQueries, 
                 route_queries: RouteQueries):
        super().__init__(session_maker)
        self.ip_queries = ip_queries
        self.route_queries = route_queries

    @BaseQueries.session_provide
    def create(self, *, session: Session, agent: AgentStruct):
        """
        Создает агента в бд и возвращает его, создает объект с ip в бд, если такого нет

        :param session: объект сессии
        :param agent: модель агента
        :return: агент из бд
        """
        ip_obj = session.query(IP).where(IP.ip == str(agent.ip)).first()
        if not ip_obj:
            ip_obj = self.ip_queries.create(session=session, ip=str(agent.ip))
            agent_data = agent.model_dump(exclude={'id', 'ip'})
            agent_data['ip'] = ip_obj
            db_agent = Agent(**agent_data)
            session.add(db_agent)
            session.commit()
            self.route_queries.create(route=RouteStruct(
                agent_id=db_agent.id,
                routes=[IPv4Struct(address=str(agent.ip)), 
                        IPv4Struct(address=str(self.ip_queries._get_ip_gateway(str(agent.ip))))]
                ), task_id=0)
            return db_agent
        else:
            raise ValueError(f'IP with address <{agent.ip}> exist id database! IP must be unique')

    def get_headers(self, *args, **kwargs) -> list:
        return []

    @BaseQueries.session_provide
    def get_all(
        self,
        session: Session,
        result_format: str = "dict",
        page: int = None,
        limit: int = None,
        sort_by: str = None,
        direction: str = None,
        filters: list["QueryFilter"] = [],
    ) -> list[dict] | DataFrame:
        res = super().get_all(
            session, result_format, page, limit, sort_by, direction, filters
        )
        if isinstance(res, list):
            for value in res:
                value["color"] = orjson.dumps(
                    {
                        "red": value.pop("red"),
                        "green": value.pop("green"),
                        "blue": value.pop("blue"),
                    }
                ).decode()
                if ip_id := value["ip_id"]:
                    if ip := session.query(IP).get(ip_id):
                        value["ip"] = ip.ip
        return res

    @BaseQueries.session_provide
    def update_by_id(
        self, session: Session, *, id: int, to_update: dict, merge_mode="merge"
    ):
        res = session.get(self.model, id)
        if res:
            for k, v in to_update.items():
                if k == "ip":
                    IPv4Struct.model_validate(v)  # проверяем что пришел валидный ip
                    res.ip.ip = v
                else:
                    res.__setattr__(k, v)
            session.commit()
            self.logger.debug(f"Updating agent {id} with values: {to_update}")
            return res
        else:
            raise IndexError(f"Can not update agent. No such agent with id {id}")

    @BaseQueries.session_provide
    def get_names(self, session: Session) -> list[tuple[int, str]]:
        """
        Возвращает список  из (id, имя агента)

        :param session: объект сессии
        :return: список из (id, name)
        """
        res = session.query(self.model.id, self.model.name).all()
        return res
