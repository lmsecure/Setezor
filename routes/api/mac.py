from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class MACView(BaseView):
    endpoint = '/mac'
    queries_path = 'mac'