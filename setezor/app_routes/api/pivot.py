from aiohttp.web import Request, Response, json_response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest

class PivotView(BaseView):
    endpoint = '/pivot'
    queries_path = 'pivot'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        pivots = db.pivot.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('ip')} for i in pivots])
    
    @BaseView.route('GET', '/node_info')
    @project_require
    async def get_node_info(self, request: PMRequest):
        """Запрос на составление сводной таблицы для ноды"""
        
        node_id = request.rel_url.query.get('ip_id')
        db = await get_db_by_session(request=request)
        data = db.pivot.get_info_about_node(ip_id=node_id)
        return json_response(status=200, data=data)