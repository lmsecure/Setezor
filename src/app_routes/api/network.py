from ipaddress import IPv4Network
from functools import lru_cache

from aiohttp.web import Response, json_response
from pydantic import BaseModel, Field, ConfigDict

from app_routes.session import project_require, get_db_by_session
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest

from network_structures import NetworkStruct
from database.models import Network

class NetResponse(BaseModel):
    
    model_config = ConfigDict(from_attributes=True, frozen=True)
    
    id: int = Field(ge=0)
    label: IPv4Network
    nodes: tuple[int, ...] = Field(default_factory=tuple)
    
class NetLink(BaseModel):
    
    from_net: int = Field(alias='from')
    to_net: int = Field(alias='to')


class NetworkView(BaseView):
    endpoint = '/network'
    queries_path = 'network'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        macs = db.mac.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('mac')} for i in macs])
    
    @BaseView.route('GET', '/{subnet}')
    async def get_subnet(self, request: PMRequest):
        """
        _summary_

        :param request: объект http запроса
        :return: список подсетей в json`e
        """
        net = request.match_info['name']
        net = NetworkStruct(network=net)
        db = await get_db_by_session(request=request)
        networks = db.network.get_subnets_structs(network=net)
        return json_response([i.model_dump() for i in networks])
    
    
    @BaseView.route('GET', '/')
    async def get_subnets(self, request: PMRequest):
        
        db = await get_db_by_session(request)
        session = db.db.create_session()
        result = db.network.get_all(session=session, result_format=None)
        result = tuple((NetResponse(id=i.id, label=i.network, nodes=(ip.id for ip in i.ip_addresses)) for i in result))
        resp = self.create_net_hierarchy(result)
        from pprint import pprint
        pprint(resp)
        return Response()
    
    @lru_cache(512)
    def create_net_hierarchy(self, networks: tuple[NetResponse]):
        
        hierarchy: dict[NetResponse, list[NetResponse]] = {}
        for network in networks:
            hierarchy[network] = []

            for other_network in networks:
                if network != other_network and network.label.subnet_of(other_network.label):
                    hierarchy[network].append(other_network)

        return hierarchy
    
    # @lru_cache(512)
    # def create_net_hierarchy(self, networks: tuple[NetResponse]):
    #     from collections import deque
    #     networks = deque(sorted(networks, key= lambda x: x.label.num_addresses))
    #     hierarchy: dict[NetResponse, list[NetResponse]] = {}
    #     while True:
    #         hierarchy[network] = []

    #         for other_network in networks:
    #             if network != other_network and other_network.label.subnet_of(network.label):
    #                 hierarchy[network].append(other_network)

    #     return hierarchy
    
    
    def create_links(self, networks: tuple[NetResponse], links: list = []):
        
        hierarchy = self.create_net_hierarchy(networks)
        for key, value in hierarchy.items():
            ...