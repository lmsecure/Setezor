from aiohttp.web import Response, Request, HTTPFound, json_response, RouteTableDef
import aiohttp_jinja2
from modules.project_manager.manager import ProjectManager
from tools.ip_tools import get_self_interfaces


project_routes = RouteTableDef()

@project_routes.get('/projects/')
async def projects_page(request: Request) -> Response:
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """    
    project_manager = ProjectManager()
    projects_names = project_manager.get_existing_projects_name()
    context = {'projects': projects_names, 'ifaces': get_self_interfaces()}
    return aiohttp_jinja2.render_template('projects.html', request=request, context=context)    