from routes.pages.info import info_routes
from routes.pages.screenshots import screenshot_routes
from routes.pages.network import network_routes
from routes.pages.project import project_routes
from aiohttp.web import UrlDispatcher


def add_page_routes(router: UrlDispatcher):
    """Регистрирует route-ы в aiohttp приложении

    Args:
        router (UrlDispatcher): router из aiohttp приложения
    """    
    router.add_routes(info_routes)
    router.add_routes(screenshot_routes)
    router.add_routes(network_routes)
    router.add_routes(project_routes)