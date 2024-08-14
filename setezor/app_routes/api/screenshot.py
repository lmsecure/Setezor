from aiohttp.web import Request, Response, json_response

from setezor.app_routes.session import project_require, get_db_by_session
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest

class ScreenshotView(BaseView):
    endpoint = '/screenshot'
    queries_path = 'screenshot'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        ips = db.screenshot.get_all()
        return json_response(status=200, data=[{'value': i.id, 'label': i.screenshot_path} for i in ips])