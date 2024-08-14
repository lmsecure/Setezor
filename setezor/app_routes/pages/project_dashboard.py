
from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session
import orjson

from setezor.app_routes.session import project_require, get_db_by_session, get_project
from setezor.modules.project_manager.manager import ProjectInfo
from setezor.modules.application import PMRequest
from setezor.tools.ip_tools import get_interfaces

project_dashboard_routes = RouteTableDef()


TO_PREPARE = ['top_ports', 'top_protocols', 'top_object_type', 'top_products']
def prepare_projects_info(info: ProjectInfo):
    # всрато подгатавливаю данные для отрисовки графиков на клиенте
    res = info.to_dict()
    for prepare_value in TO_PREPARE:
        if value:=res.get(prepare_value):
            res[prepare_value] = {'lables': orjson.dumps([i['value'] for i in value]).decode(),
                                  'data': orjson.dumps([i['count'] for i in value]).decode()}
        else:
            res[prepare_value] = ''
    return res

# @project_dashboard_routes.get('/projects_dashboard/')
# @project_require
async def project_card(request: PMRequest) -> Response:
    """Формирует html страницу выбора проекта на основе jinja2 шаблона и возвращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    session = await get_session(request=request)
    project_id = session.get('project_id')
    project = await request.app.pm.get_project(project_id)
    hide_navbar = False
    context = {'interfaces': [i.name for i in get_interfaces() if i.ip_address], 'hide_navbar': hide_navbar,
               'current_project': project.configs.variables.project_name}
    res = await request.app.pm.get_projects_info()
    res = res[0]
    res = prepare_projects_info(res)
    context = {'project_info': res}
    return aiohttp_jinja2.render_template('project_card.html', request=request, context=context)


@project_dashboard_routes.get('/projects_dashboard/')
@project_require
async def project_dashboard(request: PMRequest):
    
    project = await get_project(request=request)
    project_name = project.configs.variables.project_name
    project_id = project.configs.variables.project_id
    project_info = request.app.pm.get_project_info(project)
    db = await get_db_by_session(request)
    pivot = db.pivot
    context = {'current_project': project_name, 'current_project_id': project_id, 
                         'interfaces': [i for i in get_interfaces() if i.ip_address],
                         'project_info': prepare_projects_info(project_info),
                'tab': {'name': pivot.model.__name__.lower(), 
                    'base_url': f'/api/{pivot.model.__name__.lower()}',
                    'columns': pivot.model.get_headers_for_table()}}
    return aiohttp_jinja2.render_template('projects_dashboard.html', request=request, context=context)