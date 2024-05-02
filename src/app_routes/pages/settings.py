from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from app_routes.session import project_require, get_db_by_session, get_project

from modules.application import PMRequest
from tools.ip_tools import get_interfaces

settings_routes = RouteTableDef()

@settings_routes.get('/settings/')
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
    project_name = project.configs.variables.project_name
    project_id = project.configs.variables.project_id
    table = queries.agent
    context = {'current_project': project_name, 'current_project_id': project_id, 
                         'interfaces': [i for i in get_interfaces() if i.ip_address],
                'tab': {'name': table.model.__name__.lower(), 
                    'base_url': f'/api/{table.model.__name__.lower()}',
                    'columns': table.model.get_headers_for_table()}}
    return aiohttp_jinja2.render_template('settings.html', request=request, context=context)