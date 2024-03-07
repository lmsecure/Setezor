from uuid import uuid4
import socket

from aiohttp.web import Response, Request, HTTPFound, json_response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session

from modules.project_manager.manager import ProjectManager
from modules.application import PMRequest
from tools.ip_tools import get_interfaces

project_routes = RouteTableDef()

@project_routes.get('/projects/')
async def projects_page(request: PMRequest) -> Response:
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    session = await get_session(request=request)
    project_name = session.get('project_name')
    hide_navbar = False
    project_manager: ProjectManager = request.app.pm
    if not session.get('project_name') or session.get('project_name') == "*":
        session['project_name'] = '*'
        session['user_uuid'] = str(uuid4())
        project_manager.add_client(uuid=session.get('user_uuid'), project_name='*')
        hide_navbar = True
    projects_names = project_manager.get_exist_projects_name()
    context = {'projects': projects_names, 'interfaces': [i.name for i in get_interfaces() if i.ip_address], 'hide_navbar': hide_navbar,
               'current_project': project_name}
    return aiohttp_jinja2.render_template('projects.html', request=request, context=context)    