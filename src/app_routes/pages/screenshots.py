from aiohttp.web import Response, Request, RouteTableDef
import aiohttp_jinja2


screenshot_routes = RouteTableDef()

@screenshot_routes.get('/screenshots/')
async def screenshot_page(request: Request) -> Response:
    """Формирует html страницу отображения скриншотов на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """    
    context = {}
    return aiohttp_jinja2.render_template('screenshots.html', request=request, context=context)