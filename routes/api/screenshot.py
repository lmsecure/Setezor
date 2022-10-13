from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class ScreenshotView(BaseView):
    endpoint = '/screenshot'
    queries_path = 'screenshot'