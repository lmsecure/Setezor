from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session

from app_routes.session import project_require, get_db_by_session, get_project
from modules.application import PMRequest
from tools.ip_tools import get_interfaces

network_routes = RouteTableDef()

@network_routes.get('/network/')
@project_require
async def network_page(request: PMRequest):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    queries = await get_db_by_session(request=request)
    project = await get_project(request=request)
    is_scapy_running = project.schedulers.get('scapy').active_count
    device_types = [{'label': i.get('object_type').capitalize(), 'value': i.get('object_type')} for i in queries.object_types.get_all() ]
    ses = await get_session(request)
    project_name = ses.get('project_name')
    context = {'device_types': device_types, 'is_scapy_running': is_scapy_running, 'table': queries.port.model.get_headers_for_table(),
               'current_project': project_name, 'interfaces': [i for i in get_interfaces() if i.ip_address]}
    return aiohttp_jinja2.render_template('network/base.html', request=request, context=context)