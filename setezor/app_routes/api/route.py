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
