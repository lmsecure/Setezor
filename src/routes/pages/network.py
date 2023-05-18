from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2
from routes.session import project_require, get_db_by_session, get_project


network_routes = RouteTableDef()

@network_routes.get('/network/')
@project_require
async def network_page(request: Request):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    queries = await get_db_by_session(request=request)
    project = await get_project(request=request)
    is_scapy_running = bool(project.schedulers.get('scapy').active_count)
    device_types = [{'label': i.get('object_type').capitalize(), 'value': i.get('object_type')} for i in queries.object_types.get_all() ]
    context = {'device_types': device_types, 'start_scapy': is_scapy_running, 'table': queries.port.model.get_headers_for_table()}
    return aiohttp_jinja2.render_template('network/base.html', request=request, context=context)