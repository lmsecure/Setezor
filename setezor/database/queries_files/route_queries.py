from pydantic import BaseModel, Field, computed_field
from sqlalchemy.orm.session import Session
from ..models import Route, IP, RouteList, Agent
from .base_queries import BaseQueries

try:
    from network_structures import RouteStruct, IPv4Struct
except ImportError:
    from ...network_structures import RouteStruct, IPv4Struct

class VisEdge(BaseModel):
    
    from_node: int = Field(serialization_alias='from')
    to_node: int = Field(serialization_alias='to')
    
class VisNode(IPv4Struct):
    agents: list[int] = Field(default_factory=list, description='Список агентов, с которых видно этот ip')
    agent: int | None = Field(default=None, description='Id агента, если ip принадлежит ему')
    shape: str = 'dot'
    value: int = 1

    @computed_field
    @property
    def label(self) -> str:
        return str(self.address)

class RouteQueries(BaseQueries):
    """Класс запросов к таблице скриншотов
    """
    model = Route
    
    @BaseQueries.session_provide
    def create(self, *, session: Session, route: RouteStruct, task_id: int):
        ips = []
        for ip in route.routes:
            ip_obj = session.query(IP).where(IP.ip == str(ip.address)).first()
            if not ip_obj:
                ip_obj = IP.from_struct(ip)
                session.add(ip_obj)
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

    @BaseQueries.session_provide
    def get_routes(self, *, session: Session) -> list[RouteStruct]:
        res = session.query(Route).all()
        routes = []
        for i in res:
            i: Route
            ips = i.routes
            ips.sort(key= lambda x: x.position)
            ips = (ip.ip for ip in ips)
            ips = [IPv4Struct(
                id=ip.id,
                domain_name=ip.domain_name,
                ports=...,
                mac_address=ip._mac.mac,
                address=ip.ip
                ) for ip in ips]
            rt = RouteStruct(id=i.id, agent_id=i.agent_id, routes=ips)
            routes.append(rt)
        return routes
    
        
    @BaseQueries.session_provide
    def get_vis_edges(self, *, session: Session, routes: list[RouteStruct]): # ! заглушка
        
        routes: list[RouteStruct] = (i.to_struct() for i in session.query(Route).all())
        links: list[list[IPv4Struct]] = []
        for route in routes:
            route = route.routes
            result = [route[i:i + 2] for i in range(len(route) - 1)]
            for i in result:
                links.append(i)
                
        seen = set()
        edges: list[VisEdge] = []
        for first, second in links:
            key = str(first.address) + str(second.address)
            if key not in seen:
                seen.add(key)
                (first.id, second.id)
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
            node = ip.to_struct().model_dump()
            vis_node = VisNode.model_validate(node)
            vis_node.agents = list(set((i.route.agent_id for i in ip .route_values)))
            if agent:= session.query(Agent).where(Agent.ip_id == ip.id).first():
                vis_node.agent = agent.id
            nodes.append(vis_node)
        self.logger.debug(f'Getting {len(nodes)} vis nodes')
        return nodes
        
        
    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)