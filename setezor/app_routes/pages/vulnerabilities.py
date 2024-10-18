from aiohttp.web import Response, RouteTableDef
import aiohttp_jinja2
from setezor.app_routes.session import project_require
from setezor.modules.application import PMRequest
from setezor.app_routes.session import project_require, get_db_by_session, get_project
from setezor.database.models import Resource
resource_routes = RouteTableDef()


@resource_routes.get('/vulnerabilities/')
@project_require
async def all_resources(request: PMRequest) -> Response:
    """Формирует html страницу отображения информации из базы на основе jinja2 шаблона и возращает её

    Args:
        request (Request): объект http запроса

    Returns:
        Response: отрендеренный шаблон страницы
    """
    project = await get_project(request=request)
    project_name = project.configs.variables.project_name
    project_id = project.configs.variables.project_id
    context = {
        "tab":{
            'name':'resource_vulnerabilities',
            "base_url":"/api/resource",
            'columns': Resource.get_headers_for_table()
        },
        'current_project': project_name, 'current_project_id': project_id,
    }
    return aiohttp_jinja2.render_template('vulnerabilities.html', request=request,context=context)
