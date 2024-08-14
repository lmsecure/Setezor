from aiohttp.web import Response, json_response, json_response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest

from setezor.network_structures import NetworkStruct

class NetworkView(BaseView):
    endpoint = '/network'
    queries_path = 'network'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        macs = db.mac.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('mac')} for i in macs])
    
    @BaseView.route('GET', '/root_networks')
    async def get_root_subnets(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        res = db.network.get_root_networks()
        networks = [i.model_dump() for i in res]
        return json_response(networks)
    
    @BaseView.route('GET', '/{subnet}')
    async def get_subnets(self, request: PMRequest):
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