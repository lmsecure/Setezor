from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2
from routes.session import project_require


network_routes = RouteTableDef()

@network_routes.get('/network/')
@project_require
async def network_page(request: Request):
    """Формирует html страницу отображения топологии сети на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """    
    context = {}
    return aiohttp_jinja2.render_template('network.html', request=request, context=context)