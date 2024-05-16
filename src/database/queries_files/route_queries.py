import re
from typing import ClassVar
from functools import lru_cache

from pydantic import BaseModel, computed_field, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError
from sqlalchemy.orm.session import Session
from ..models import Route, IP, RouteList, Agent
from .base_queries import BaseQueries
from .ip_queries import IPQueries

try:
    from network_structures import RouteStruct, IPv4Struct
except ImportError:
    from ...network_structures import RouteStruct, IPv4Struct

class VisEdge(BaseModel):
    
    from_node: int = Field(serialization_alias='from')
    to_node: int = Field(serialization_alias='to')

class VisIcon(BaseModel):
    """Класс иконки для виза"""
    
    face: str
    code: str
    size: int = Field(gt=0)
    color: str = '#2B7CE9'
    
    __color_re: ClassVar[re.Pattern] = re.compile('^#[0-9a-zA-Z]{6}$')
    
    @field_validator('color', mode='after')
    def validate_color(cls, color: str):
        res = cls.__color_re.search(color)
        if res is None:
            raise PydanticCustomError('Icon code validation error', 
                                      f'Code must be like "{cls.__color_re.pattern}"')
        return color

class VisNetwork(BaseModel):
    
    """
    Объект ноды, содержит сеть, а так же список id`шников нод
    """
    label: str
    nodes: list[int] = Field(default_factory=list)

class VisNode(IPv4Struct):
    agents: list[int] = Field(default_factory=list, description='Список агентов, с которых видно этот ip')
    agent: int | None = Field(default=None, description='Id агента, если ip принадлежит ему')
    shape: str = 'dot'
    value: int = 1
    icon: None | VisIcon = Field(default=None)
    is_gateway: bool = False
    is_guess: bool = False
    network: VisNetwork | None = None

    @computed_field
    @property
    def label(self) -> str:
        return str(self.address)
    
    @model_validator(mode='after')
    def post_validator(self):
        if self.icon:
            self.shape = 'icon'
        return self
    
    def __hash__(self):
        return hash(self.id)


#! По хорошему слой обработки vis`a должен быть вынесен
GATEWAY_ICON = VisIcon(face="Glyphter", code='\u0041', size=60)
GATEWAY_ICON_DICT = GATEWAY_ICON.model_dump()

AGENT_ICON = VisIcon(face="bootstrap-icons", size=65, code='\uF591')
AGENT_ICON_DICT = AGENT_ICON.model_dump()

class RouteQueries(BaseQueries):
    """Класс запросов к таблице роутов
    """
    model = Route
    
    def __init__(self, session_maker: Session, ip_queries: IPQueries):
        super().__init__(session_maker)
        self.ip_queries = ip_queries
    
    @BaseQueries.session_provide
    def create(self, *, session: Session, route: RouteStruct, task_id: int):
        ips: list[IP] = []
        for ip in route.routes:
            ip_obj = session.query(IP).where(IP.ip == str(ip.address)).first()
            if not ip_obj:
                ip_obj = self.ip_queries.create(session=session, ip=str(ip.address))
            ips.append(ip_obj)
        rt = session.query(Route).where(Route.routes)
        db_route = Route(agent_id=route.agent_id, task_id=task_id)
        session.add(db_route)
        for ind, ip in enumerate(ips):
            rt = RouteList(route=db_route, ip=ip, position=ind)
            session.add(rt)
        session.commit()
        self.logger.debug(f'Creating route {route}')
        return db_route
    
    def create_icon(self, ip: IP):
        if ip.network_if_gateway:
            return GATEWAY_ICON
        elif ip.agent:
            return AGENT_ICON

    def __create_vis_node(self, ip: IP):
        node = VisNode(
            id=ip.id,
            domain_name=ip.domain_name,
            ports=[p.to_struct() for p in ip._host_ip] if ip._host_ip else [],
            mac_address=ip._mac.mac,
            address=ip.ip,
            is_guess=ip.network.guess if ip.network else False,
            is_gateway=True if ip.network_if_gateway else False,
            icon=self.create_icon(ip),
            agents=list(set((i.route.agent_id for i in ip.route_values))),
            agent=ip.agent.id if ip.agent else None,
            )
        return node
    
    @BaseQueries.session_provide
    def get_routes(self, *, session: Session) -> list[list[VisNode]]:
        res = session.query(Route).all()
        routes: list[list[VisNode]] = []
        for i in res:
            i: Route
            ips = i.routes
            ips.sort(key= lambda x: x.position)
            ips = [ip.ip for ip in ips]
            seen = set[int]()
            result_rt = list[VisNode]()
            for ip in ips:
                if ip.id in seen:
                    continue
                gateway = ip.network.gateway if ip.network else None
                if gateway and gateway.id not in seen:
                    node = self.__create_vis_node(gateway)
                    seen.add(node.id)
                    result_rt.append(node)
                    if node.id != ip.id:
                        routes.append((node, self.__create_vis_node(ip)))
                else:
                    node = self.__create_vis_node(ip)
                    seen.add(node.id)
                    if node.is_gateway and not node.agents:
                        node.agents.append(i.agent_id)
                    result_rt.append(node)
            routes.append(tuple((i for i in result_rt)))
        routes = tuple((i for i in routes))
        routes = self._delete_short_ways(routes)
        return routes
    
    @lru_cache()
    def _is_exist_long_way(self, route: tuple[VisNode], long_routes: tuple[tuple[int]]):
        
        all_routes_ids = set(long_routes)
        for rt in long_routes:
            all_routes_ids.add(tuple(reversed([i for i in rt])))
        for rt in long_routes:
            if route in all_routes_ids:
                return True
        return False
    
    @lru_cache()
    def _delete_short_ways(self, routes: tuple[tuple[VisNode]]):
        """Удаляет короткие маршруты"""
        routes_ids = {ind: rt for ind, rt in enumerate(routes)}
        short_routes = {k: v for k, v in routes_ids.items() if len(v) == 2}
        long_routes = {k: v for k, v in routes_ids.items() if len(v) != 2}
        
        prepared_long_routes = []
        for rt in long_routes.values():
            prepared_long_routes.append((rt[0].id, rt[-1].id))
            prepared_long_routes.append((rt[-1].id, rt[0].id))
        to_del = set()
        for ind, rt in short_routes.items():
            if self._is_exist_long_way((rt[0].id, rt[1].id), tuple(prepared_long_routes)):
                to_del.add(ind)
        res = [v for k, v in routes_ids.items() if k not in to_del]
        return res
            
    
        
    @BaseQueries.session_provide
    def get_vis_edges(self, *, session: Session): # ! заглушка
        
        # routes: list[RouteStruct] = (i.to_struct() for i in session.query(Route).all())
        routes = self.get_routes(session=session)
        seen = set()
        edges: list[VisEdge] = []
        for route in routes:
            result = [route[i:i + 2] for i in range(len(route) - 1)] # сплит всего роута на линки
            for i in result:
                first = i[0]
                second = i[1]
                key = str(first.address) + str(second.address)
                if key not in seen:
                    seen.add(key)
                    seen.add(str(second.address) + str(first.address))
                    edges.append(VisEdge(from_node=first.id, to_node=second.id))
        self.logger.debug(f'Getting {len(edges)} vis edges')
        return edges
    
    @BaseQueries.session_provide
    def get_vis_nodes(self, *, session: Session) -> list[VisNode]:
        """
        Собирает все ip из для отправки на фронт

        :param session: сессия алхимии
        :return: (дикт агентов, дикт ip)
        """
        ips: list[IP] = session.query(IP).all()
        nodes = []
        for ip in ips:
            node = self.__create_vis_node(ip)
            nodes.append(node)
        self.logger.debug(f'Getting {len(nodes)} vis nodes')
        return nodes
        
        
    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)
    
    @BaseQueries.session_provide
    def delete_link(self, *, session: Session, first_ip: int, to_ip: int):
        """
        Запрос на удаление ноды

        :param first_ip: id первого ip
        :param to_ip: id первого ip
        """
        
        #! todo