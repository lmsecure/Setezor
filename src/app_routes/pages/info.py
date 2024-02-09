from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session

from app_routes.session import project_require, get_db_by_session
from modules.application import PMRequest

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
    ses = await get_session(request)
    project_name = ses.get('project_name')
    context = {'tabs': [{'name': i.model.__name__.lower(), 
                         'base_url': f'/api/{i.model.__name__.lower()}',
                         'columns': i.model.get_headers_for_table()} for i in [db.object, db.l3link, db.pivot, db.task]],
                'current_project': project_name}
    
    return aiohttp_jinja2.render_template('info_tables.html', request=request, context=context)
