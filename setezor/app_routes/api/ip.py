from aiohttp.web import Request, Response, json_response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest
from setezor.tools.ip_tools import get_ipv4

class IPView(BaseView):
    endpoint = '/ip'
    queries_path = 'ip'
    
    @BaseView.route('GET', '/vis/{id}')
    async def get_by_id(self, request: PMRequest) -> Response:
        ip_id = int(request.match_info.get('id'))
        db_entity = await self.get_db_queries(request=request)
        node = db_entity.get_by_id(id=ip_id, return_format='vis')
        return json_response(status=200, data={'status': True, 'node': node})
        
    @BaseView.route('GET', '/vis')
    @project_require
    async def get_edges(self, request: PMRequest) -> Response:
        """Метод получения узлов для построения топологии сети

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        db = await get_db_by_session(request=request)
        return json_response(status=200, data={'status': True, 'nodes': db.ip.get_vis_nodes()})
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        ips = db.ip.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('ip')} for i in ips])
    
    @BaseView.route('GET', '/interface_ip')
    @project_require
    async def get_interface_ip(self, request: PMRequest):
        
        iface = request.query['iface']
        res = get_ipv4(iface)
        return Response(body=res)