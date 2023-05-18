from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class IPView(BaseView):
    endpoint = '/ip'
    queries_path = 'ip'
    
    @BaseView.route('GET', '/vis/{id}')
    async def get_by_id(self, request: Request) -> Response:
        ip_id = int(request.match_info.get('id'))
        db_entity = await self.get_db_queries(request=request)
        node = db_entity.get_by_id(id=ip_id, return_format='vis')
        return json_response(status=200, data={'status': True, 'node': node})
        
    @BaseView.route('GET', '/vis')
    @project_require
    async def get_edges(self, request: Request) -> Response:
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
    async def all_short(self, request: Request):
        db = await get_db_by_session(request=request)
        ips = db.ip.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('ip')} for i in ips])