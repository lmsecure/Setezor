from aiohttp.web import Request, Response, json_response
from routes.session import project_require, get_db_by_session
from routes.api.base_web_view import BaseView


class ObjectView(BaseView):
    endpoint = '/object'
    queries_path = 'object'
    
    @BaseView.route('PUT', '/')
    async def update(self, request: Request):
        db_entity = await self.get_db_queries(request=request)
        params = await request.json()
        db_entity.update_by_ip_id(ip_id=params.get('ip_id'), to_update=params.get('to_update'))
        return json_response(status=200, data={'status': 'ok'})
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: Request):
        db = await get_db_by_session(request=request)
        objects = db.object.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('object_type')} for i in objects])