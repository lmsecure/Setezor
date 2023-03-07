from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class MACView(BaseView):
    endpoint = '/mac'
    queries_path = 'mac'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: Request):
        db = await get_db_by_session(request=request)
        macs = db.mac.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('mac')} for i in macs])