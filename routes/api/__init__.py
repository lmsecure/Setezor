from routes.api.ip import IPView
from routes.api.l3link import L3LinkView
from routes.api.mac import MACView
from routes.api.object import ObjectView
from routes.api.port import PortView
from routes.api.project import ProjectView
from routes.api.screenshot import ScreenshotView
from routes.api.task import TaskView
from aiohttp.web import UrlDispatcher

endpoint = '/api'

def add_api_routes(router: UrlDispatcher) -> None:
    """Регистрирует декорированные методы api в aiohttp сервере

    Args:
        router (UrlDispatcher): router из aiohttp приложения
    """    
    for cls in [IPView, L3LinkView, MACView, ObjectView, PortView, ProjectView, ScreenshotView, TaskView]:  # для каждого класса api
        obj = cls(endpoint)  # создадим класс с endpoint-ом 
        for i in dir(obj):  # для каждого имени атрибута класса
            attr = obj.__getattribute__(i)  # получим атрибут
            if callable(attr):  # если это функция
                if attr.__name__ == 'route_wrapper':  # и эта функция обернута декоратором с именем "route_wrapper"
                    router.add_route(**attr())  # зарегистрируем эту функцию с методом, по пути пример вызова {'GET', '/api/ip/all', <func обработчик вызова>}