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
    def delete_edges(self, *, session: Session, route: RouteStruct, task_id: int):
        db_route = session.query(Route).filter(Route.agent_id == route.agent_id).first()

        if not db_route:
            self.logger.warning(f'Route with agent_id {route.agent_id}')
            return None

        ips_to_delete = []

        for ip in route.routes:
            ip_obj = session.query(RouteList).filter(RouteList.route_id == str(RouteStruct)).first()
            if ip_obj:
                ips_to_delete.append(ip_obj)

        for ip_obj in ips_to_delete:
            session.delete(ip_obj)
        session.delete(db_route)
        session.commit()
        self.logger.debug(f'Removal of route {db_route} successful.')
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
    def get_vis_edges(self, *, session: Session): # ! заглушка
        res = session.query(Route,RouteList,IP)\
            .join(RouteList,Route.id == RouteList.route_id)\
            .join(IP,RouteList.value == IP.id).order_by(Route.id,RouteList.position)
        res = res.all()
        if not res:
            return []
        links = []
        for i in range(len(res) - 1):
            if res[i].Route.id == res[i+1].Route.id:
                links.append((res[i],res[i+1]))
        seen = set()
        edges: list[VisEdge] = []
        for first, second in links:
            key = str(first.IP.ip) + str(second.IP.ip)
            if key not in seen:
                seen.add(key)
                edges.append(VisEdge(from_node=first.IP.id, to_node=second.IP.id))
        self.logger.debug(f'Getting {len(edges)} vis edges')
        return edges
    
    @BaseQueries.session_provide
    def get_vis_nodes(self, *, session: Session) -> list[VisNode]:
        """
        Собирает все ip из для отправки на фронт

        :param session: сессия алхимии
        :return: (дикт агентов, дикт ip)
        """
        res = session.query(IP,RouteList,Route)\
            .join(RouteList,IP.id == RouteList.value,isouter=True)\
            .join(Route,Route.id == RouteList.route_id,isouter=True)\
            .join(Agent,Agent.ip_id == IP.id,isouter=True)\
            .with_entities(IP.ip,Route.agent_id,Agent.id).distinct().all()
        agents_ips = {}
        for row in res:
            address = row[0]
            agent_id = row[1]
            agent = row[2]
            if not agents_ips.get(address):
                agents_ips[address] = {
                    "agents": set(),
                    "agent": None
                }
                if agent_id:
                    agents_ips[address].update({"agents": {agent_id}})
                if agent:
                    agents_ips[address].update({"agent": agent})
            else:
                if agent_id:
                    agents_ips[address]["agents"].add(agent_id)
                if agent:
                    agents_ips[address]["agent"] = agent
        ips: list[IP] = session.query(IP).all()
        nodes = []
        for ip in ips:
            node = ip.to_struct().model_dump()
            vis_node = VisNode.model_validate(node)
            vis_node.agents = list(agents_ips[ip.ip]["agents"])
            vis_node.agent = agents_ips[ip.ip]["agent"]
            nodes.append(vis_node)
        self.logger.debug(f'Getting {len(nodes)} vis nodes')
        return nodes

    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)