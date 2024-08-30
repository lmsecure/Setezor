from .info import info_routes
from .screenshots import screenshot_routes
from .network_map import network_map_routes
from .tool import tool_routes
from .project import project_routes
from.project_dashboard import project_dashboard_routes
from .settings import settings_routes
from aiohttp.web import UrlDispatcher



def add_page_routes(router: UrlDispatcher):
    """Регистрирует route-ы в aiohttp приложении

    Args:
        router (UrlDispatcher): router из aiohttp приложения
    """    
    router.add_routes(info_routes)
    router.add_routes(screenshot_routes)
    router.add_routes(network_map_routes)
    router.add_routes(tool_routes)
    router.add_routes(project_routes)
    router.add_routes(project_dashboard_routes)
    router.add_routes(settings_routes)