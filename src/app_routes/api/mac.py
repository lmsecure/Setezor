from aiohttp.web import Request, Response, json_response

from app_routes.session import project_require, get_db_by_session
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest
from tools.ip_tools import get_mac

class MACView(BaseView):
    endpoint = '/mac'
    queries_path = 'mac'
    
    @BaseView.route('GET', '/all_short')
    @project_require
    async def all_short(self, request: PMRequest):
        db = await get_db_by_session(request=request)
        macs = db.mac.get_all()
        return json_response(status=200, data=[{'value': i.get('id'), 'label': i.get('mac')} for i in macs])
    
    @BaseView.route('GET', '/interface_mac')
    @project_require
    async def get_interface_ip(self, request: PMRequest):
        
        iface = request.query['iface']
        res = get_mac(iface)
        return Response(body=res)