from aiohttp.web import Request, Response, json_response


from setezor.app_routes.session import project_require, get_db_by_session, get_project
from setezor.app_routes.api.base_web_view import BaseView
from setezor.modules.application import PMRequest

from setezor.tools.json_tools import orjson_dumps
from setezor.network_structures import RouteStruct, IPv4Struct


class RouteView(BaseView):
    endpoint = "/route"
    queries_path = "route"

    @BaseView.route("get", "/vis_edges")
    @project_require
    async def get_vis_edges(self, request: PMRequest):
        db = await get_db_by_session(request)
        edges = db.route.get_vis_edges()
        edges = [i.model_dump(by_alias=True) for i in edges]
        return json_response(edges, dumps=orjson_dumps)

    @BaseView.route("get", "/vis_nodes")
    @project_require
    async def get_vis_nodes(self, request: PMRequest):

        db = await get_db_by_session(request)
        nodes = db.route.get_vis_nodes()
        nodes = [i.model_dump() for i in nodes]
        return json_response(nodes, dumps=orjson_dumps)

    @BaseView.route("POST", "/vis_add_edges")
    @project_require
    async def create_edge(self, request: PMRequest):
        project = await get_project(request)
        db = await get_db_by_session(request=request)
        resp_data = await request.json()
        first_ip = resp_data.get("first_ip")
        second_ip = resp_data.get("second_ip")
        agent_id = resp_data.get("agent_id")
        first_ip = IPv4Struct(address=resp_data.get('first_ip'))
        second_ip = IPv4Struct(address=resp_data.get('second_ip'))
        routes = RouteStruct(routes=[first_ip, second_ip], agent_id=agent_id)
        db.route.create(route=routes, task_id=None)
        return Response(status=200)

    @BaseView.route('DELETE', '/delete_edge')
    @project_require
    async def delete_edge(self, request: PMRequest):
        
        project = await get_project(request)
        db = await get_db_by_session(request=request)
        resp_data = await request.json()
        first_ip = resp_data.get('first_ip')
        second_ip = resp_data.get('second_ip')
        agent_id = resp_data.get("agent_id")
        first_ip_struct = IPv4Struct(address=resp_data.get('first_ip'))
        second_ip_struct = IPv4Struct(address=resp_data.get('second_ip'))
        routes = RouteStruct(routes=[first_ip_struct, second_ip_struct], agent_id=agent_id)
        db.route.delete_edges(route=routes, task_id=None, first_ip=first_ip, second_ip=second_ip)
        return Response()