from aiohttp.web import Request, Response, json_response

from app_routes.session import project_require
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest
from tools.ip_tools import get_interfaces

class InterfaceView(BaseView):
    endpoint = '/interface'
    queries_path = 'interface'
    
    @BaseView.route('GET', '/interfaces')
    @project_require
    async def get_edges(self, request: PMRequest) -> Response:
        
        """Получение информации о сетевых интерфейсах"""
        interfaces = get_interfaces()
        res = []
        for i in interfaces:
            if i.ip_address:
                res.append(i.to_dict())
        
        return json_response(status=200, data={'interfaces': res})
