from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView
import json


class PortView(BaseView):
    endpoint = '/port'
    queries_path = 'port'
 
    @BaseView.route('GET', '/by_ip_id')
    @project_require
    async def get_port_by_ip(self, request: Request) -> Response:
        """Метод получения портов по идентификатору ip

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """
        ip = [int(i) for i in json.loads(request.rel_url.query.get('ip_ids'))]
        db = await get_db_by_session(request)
        data = db.port.get_ports_by_ip(ip_ids=ip)
        return json_response(status=200, data=data)
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: Request):
        db = await get_db_by_session(request=request)
        ports = db.port.get_all()
        return json_response(status=200, data=[{'value': i.id, 'label': i.port} for i in ports])