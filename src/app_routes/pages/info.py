from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session

from app_routes.session import project_require, get_db_by_session, get_project
from modules.application import PMRequest
from tools.ip_tools import get_interfaces

info_routes = RouteTableDef()

@info_routes.get('/info/')
@project_require
async def info_page(request: PMRequest) -> Response:
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """    
    db = await get_db_by_session(request)
    project = await get_project(request=request)
    project_name = project.configs.variables.project_name
    project_id = project.configs.variables.project_id
    context = {'tabs': [{'name': i.model.__name__.lower(), 
                         'base_url': f'/api/{i.model.__name__.lower()}',
                         'columns': i.model.get_headers_for_table()} for i in [db.object, db.l3link, db.ip, db.mac, db.port, db.task, db.pivot]], #! Добавить db.network как будет готово
                'current_project': project_name, 'current_project_id': project_id,
                'interfaces': [i for i in get_interfaces() if i.ip_address]}
    
    return aiohttp_jinja2.render_template('info_tables.html', request=request, context=context)
