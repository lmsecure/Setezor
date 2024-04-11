from .ip import IPView
from .l3link import L3LinkView
from .mac import MACView
from .object import ObjectView
from .port import PortView
from .project import ProjectView
from .screenshot import ScreenshotView
from .pivot import PivotView
from .task import TaskView
from .report import ReportsView
from .websocket import WebSocketView
from .interface import InterfaceView
from .network import NetworkView
from aiohttp.web import UrlDispatcher

endpoint = '/api'

def add_api_routes(router: UrlDispatcher) -> None:
    """Регистрирует декорированные методы api в aiohttp сервере

    Args:
        router (UrlDispatcher): router из aiohttp приложения
    """    
    for cls in [IPView, L3LinkView, MACView, ObjectView, PortView, ProjectView, ScreenshotView, 
                TaskView, WebSocketView, ReportsView, InterfaceView, PivotView, NetworkView]:  # для каждого класса api
        obj = cls(endpoint)  # создадим класс с endpoint-ом 
        for i in dir(obj):  # для каждого имени атрибута класса
            attr = obj.__getattribute__(i)  # получим атрибут
            if callable(attr):  # если это функция
                if attr.__name__ == 'route_wrapper':  # и эта функция обернута декоратором с именем "route_wrapper"
                    router.add_route(**attr())  # зарегистрируем эту функцию с методом, по пути пример вызова {'GET', '/api/ip/all', <func обработчик вызова>}