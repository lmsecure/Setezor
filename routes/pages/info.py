from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2
from routes.session import project_require, get_db_by_session


info_routes = RouteTableDef()

@info_routes.get('/info/')
@project_require
async def info_page(request: Request) -> Response:
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """    
    db = await get_db_by_session(request)
    context = {'tabs': [{'name': i.model.__name__.lower(), 
                         'base_url': f'/api/{i.model.__name__.lower()}',
                         'columns': i.model.get_headers_for_table()} for i in [db.object, db.mac, db.ip, db.l3link, db.port, db.task]]}
    return aiohttp_jinja2.render_template('info_tables.html', request=request, context=context)
