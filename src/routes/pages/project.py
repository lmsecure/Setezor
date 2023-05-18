from aiohttp.web import Response, Request, HTTPFound, json_response, RouteTableDef
import aiohttp_jinja2
from modules.project_manager.manager import ProjectManager
from aiohttp_session import get_session
from uuid import uuid4
import socket


project_routes = RouteTableDef()

@project_routes.get('/projects/')
async def projects_page(request: Request) -> Response:
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    session = await get_session(request=request)
    project_manager: ProjectManager = request.app.pm
    if not session.get('project_name') and not session.get('user_uuid'):
        session['project_name'] = '*'
        session['user_uuid'] = str(uuid4())
        project_manager.add_client(uuid=session.get('user_uuid'), project_name='*')
    projects_names = project_manager.get_exist_projects_name()
    context = {'projects': projects_names, 'ifaces': [name for index, name in socket.if_nameindex()]}
    return aiohttp_jinja2.render_template('projects.html', request=request, context=context)    