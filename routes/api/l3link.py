from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView
from datetime import datetime
import traceback


class L3LinkView(BaseView):
    endpoint = '/l3link'
    queries_path = 'l3link'
    
    @BaseView.route('GET', '/vis')
    @project_require
    async def get_edges(self, request: Request) -> Response:
        """Метод получения граней для построения топологии сети

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        db = await get_db_by_session(request=request)
        return json_response(status=200, data={'status': True, 'edges': db.l3link.get_vis_edges()})
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: Request):
        raise NotImplementedError()