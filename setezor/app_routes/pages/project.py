from uuid import uuid4
import socket

from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session, SESSION_KEY, STORAGE_KEY
import orjson

from setezor.app_routes.pages.project_dashboard import prepare_projects_info
from setezor.app_routes.session import get_db_by_session
from setezor.modules.project_manager.manager import ProjectManager
from setezor.modules.application import PMRequest
from setezor.tools.ip_tools import get_interfaces

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
    all_project_info = await request.app.pm.get_projects_info()

    projects = [i.to_dict() for i in all_project_info]
    projects_data = orjson.dumps(projects).decode()
    context = {'projects': projects, 'interfaces': [i.name for i in get_interfaces() if i.ip_address], 'hide_navbar': hide_navbar,
               'current_project': project_id, 'projects_data': projects_data}

    return aiohttp_jinja2.render_template('projects/base_project.html', request=request, context=context)