from aiohttp.web import Request, Response, json_response
from pydantic import BaseModel

from app_routes.session import project_require, get_project
from app_routes.api.base_web_view import BaseView
from modules.application import PMRequest
from tools.ip_tools import get_interfaces, get_default_interface
from network_structures import InterfaceStruct
from tools.json_tools import orjson_dumps


class InterfaceResponse(BaseModel):
    interfaces: list[InterfaceStruct]
    default_interface: int


class InterfaceView(BaseView):
    endpoint = "/interface"
    queries_path = "interface"

    @BaseView.route("GET", "/interfaces")
    @project_require
    async def get_interfaces(self, request: PMRequest) -> Response:
        """Получение информации о сетевых интерфейсах"""
        interfaces = get_interfaces()
        project = await get_project(request)
        default = project.configs.variables.default_interface['id']
        resp = InterfaceResponse(interfaces=interfaces, default_interface=default)
        return json_response(status=200, data=resp.model_dump(), dumps=orjson_dumps)

    @BaseView.route("PUT", "/set_default")
    @project_require
    async def set_default(self, request: PMRequest) -> Response:
        """
        Устанавливает дефолтный интерфейс, принимает id интерфейса в параметрах
        """

        iface_id = request.rel_url.query.get("interface_id")
        if not iface_id:
            return Response(body="You must specify interface_id", status=423)
        try:
            iface_id = int(iface_id)
        except Exception:
            return Response(body="Interface id must be int", status=423)
        
        project = await get_project(request)
        ifaces = get_interfaces()
        iface = next((i for i in ifaces if i.id == iface_id), None)
        if iface is None:
            return Response(status=404, body=f'No such interface with id {iface_id}')
        project.configs.variables.default_interface = iface.model_dump()
        project.configs.save_config_file()
        return Response()
