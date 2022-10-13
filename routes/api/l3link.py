from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class L3LinkView(BaseView):
    endpoint = '/l3link'
    queries_path = 'l3link'
    
    @BaseView.route('GET', '/nodes_and_edges')
    @project_require
    async def get_nodes_and_edges(self, request: Request) -> Response:
        """Метод получения узлов и граней для построения топологии сети

        Args:
            request (Request): объект http запроса

        Returns:
            Response: json ответ
        """        
        db = await get_db_by_session(request=request)
        nodes_and_edges = db.l3link.get_nodes_and_edges()
        return json_response(status=200, data={'status': True, 'data': nodes_and_edges})