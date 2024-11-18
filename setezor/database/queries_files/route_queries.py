from pydantic import BaseModel, Field, computed_field
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import aliased
from sqlalchemy import select, join, alias, and_, asc
from ..models import Route, IP, RouteList, Agent, Network
from .base_queries import BaseQueries
from ..queries_files.ip_queries import IPQueries

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
    group: str = '1'

    @computed_field
    @property
    def label(self) -> str:
        return str(self.address)

class RouteQueries(BaseQueries):
    """Класс запросов к таблице скриншотов
    """
    model = Route

    def __init__(self, session_maker: Session, ip: IPQueries):
        super().__init__(session_maker)
        self.ip = ip  
    
    @BaseQueries.session_provide
    def create(self, *, session: Session, route: RouteStruct, task_id: int):
        ips = []
        for ip in route.routes:
            ip_obj = self.ip.get_or_create(session=session, ip=str(ip.address))
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
    def create_by_ipid(self, *, session: Session, agent_id: int, ip_obj_lst: list[int], task_id: int):
        db_route = Route(agent_id=agent_id, task_id=task_id)
        session.add(db_route)
        for ind, ipid in enumerate(ip_obj_lst):
            rt = RouteList(route=db_route, ip_id=ipid, position=ind)
            session.add(rt)
        session.commit()
        return db_route
    
    @BaseQueries.session_provide
    def get_routes_by_ipid_on_start_position(self, *, session: Session, ip_id: int) -> list:
        route_ids = (select(RouteList.route_id).where(RouteList.position == 0, RouteList.ip_id == ip_id)).alias("new_t")
        q = (select(RouteList).join(route_ids, RouteList.route_id == route_ids.c.route_id))
        ans = session.execute(q).scalars()
        result = []
        tmp = []
        for row in ans:
            if row.position == 0:
                if tmp:
                    result.append(tmp)
                tmp = [row.ip_id]
            else:
                tmp.append(row.ip_id)
        result.append(tmp)
        return result
        

    @BaseQueries.session_provide
    def delete_edges(self, *, session: Session, route: RouteStruct, task_id: int, first_ip, second_ip):
        """В таблице route_list находятся route_id где есть первый и второй ip_id,
        затем удаляется строка со вторым ip в найденных route_id """
        
        ip_id1 = session.query(IP).where(IP.ip == first_ip).first()
        ip_id2 = session.query(IP).where(IP.ip == second_ip).first()
        my_alias = aliased(RouteList)
        routes = session.query(RouteList).filter(RouteList.ip_id == ip_id2.id).all()
        route_ids_to_update = [route.route_id for route in routes]
        res = session.query(RouteList, my_alias).filter(
            RouteList.route_id == my_alias.route_id,
            RouteList.ip_id == ip_id1.id,
            my_alias.ip_id == ip_id2.id,
            RouteList.position < my_alias.position
        ).all()

        if route_ids_to_update:
            session.query(RouteList).filter(
                RouteList.route_id.in_(route_ids_to_update),
                RouteList.position > my_alias.position
            ).update(
                {"position": RouteList.position - 1},
                synchronize_session=False
            )
        for _from, _to in res:
            session.delete(_to)
        session.commit()
        session.close()

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

        rl1 = aliased(RouteList)
        rl2 = aliased(RouteList)

        join_condition = and_(rl1.route_id == rl2.route_id, rl1.position + 1 == rl2.position)
        query = (
            select(rl1.route_id, rl1.ip_id.label("_from"), rl2.ip_id.label("_to"))
            .select_from(join(rl1, rl2, join_condition)))
        res = session.execute(query)
        
        seen = set()
        edges: list[VisEdge] = []
        for row in res:
            key = (row._from, row._to)
            if key not in seen:
                edges.append(VisEdge(from_node=row._from, to_node=row._to))
                seen.add((key))
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
            .join(RouteList,IP.id == RouteList.ip_id,isouter=True)\
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
        ips: list[IP] = session.query(IP, Network).join(Network, IP.network_id == Network.id).all()
        nodes = []
        for ip, network in ips:
            node = ip.to_struct().model_dump()
            vis_node = VisNode.model_validate(node)
            vis_node.agents = list(agents_ips[ip.ip]["agents"])
            vis_node.agent = agents_ips[ip.ip]["agent"]
            vis_node.group = network.network
            nodes.append(vis_node)
        self.logger.debug(f'Getting {len(nodes)} vis nodes')
        return nodes

    def get_headers(self, *args, **kwargs) -> list:
        return super().get_headers(*args, **kwargs)