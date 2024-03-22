from uuid import uuid4
import socket

from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session, SESSION_KEY, STORAGE_KEY
import orjson

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
    project_id = session.get('project_id')
    hide_navbar = False
    project_manager: ProjectManager = request.app.pm
    if not project_id:
        session['project_id'] = project_manager.mock.configs.variables.project_id
        session['user_uuid'] = str(uuid4())
        await project_manager.add_client(uuid=session.get('user_uuid'), project_id=project_manager.mock.configs.variables.project_id)
        hide_navbar = True
    if project_id == '*':
        hide_navbar = True
    projects = await project_manager.project_storage.get_projects()
    projects = [{'project_id': i.configs.variables.project_id, 'project_name': i.configs.variables.project_name} for i in projects if i.configs.variables.project_name != '*']
    projects_data = orjson.dumps(projects).decode()
    context = {'projects': [i['project_name'] for i in projects], 'interfaces': [i.name for i in get_interfaces() if i.ip_address], 'hide_navbar': hide_navbar,
               'current_project': project_id, 'projects_data': projects_data}
    return aiohttp_jinja2.render_template('projects.html', request=request, context=context)    