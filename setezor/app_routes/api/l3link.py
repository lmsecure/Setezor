from datetime import datetime
import traceback

from aiohttp.web import Request, Response, json_response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest

class L3LinkView(BaseView):
    # Deprecated class
    endpoint = '/l3link'
    queries_path = 'l3link'
    
    # @BaseView.route('GET', '/vis')
    # @project_require
    # async def get_edges(self, request: PMRequest) -> Response:
    #     """Метод получения граней для построения топологии сети

    #     Args:
    #         request (Request): объект http запроса

    #     Returns:
    #         Response: json ответ
    #     """        
    #     db = await get_db_by_session(request=request)
    #     return json_response(status=200, data={'status': True, 'edges': db.l3link.get_vis_edges()})
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        raise NotImplementedError()
    
    
    @BaseView.route('PUT', '/create_edge')
    @project_require
    async def create_edge(self, request: PMRequest):
        
        db = await get_db_by_session(request=request)
        resp_data = await request.json()
        first_ip = resp_data.get('first_ip')
        second_ip = resp_data.get('second_ip')
        db.l3link.create_by_ip(first_ip=first_ip, second_ip=second_ip)
        
        return Response()
    
    
    @BaseView.route('DELETE', '/delete_edge')
    @project_require
    async def delete_edge(self, request: PMRequest):
        
        db = await get_db_by_session(request=request)
        
        resp_data = await request.json()
        first_ip = resp_data.get('first_ip')
        second_ip = resp_data.get('second_ip')
        db.l3link.delete_by_ip(first_ip=first_ip, second_ip=second_ip)
        
        return Response()