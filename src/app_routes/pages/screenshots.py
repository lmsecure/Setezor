from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from aiohttp_session import get_session

from modules.application import PMRequest

screenshot_routes = RouteTableDef()

@screenshot_routes.get('/screenshots/')
async def screenshot_page(request: PMRequest) -> Response:
    """Формирует html страницу отображения скриншотов на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    ses = await get_session(request)
    project_name = ses.get('project_name')
    context = {'current_project': project_name}
    return aiohttp_jinja2.render_template('screenshots.html', request=request, context=context)