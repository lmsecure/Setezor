from asyncio.events import AbstractEventLoop
from logging import Logger
from typing import Any, Iterable, Mapping

from aiohttp.web import Application
from aiohttp.log import web_logger
from aiohttp.web_app import _Middleware
from aiohttp.web_urldispatcher import UrlDispatcher

from ..project_manager.manager import ProjectManager


class PMApplication(Application):
    
    """Кастомный класс приложения, дополнительно принимает:
        - project_manager
        - port
        - base_path
    """
    
    def __init__(self, *, project_manager: ProjectManager, port: int, base_path: str,
                 logger: Logger = web_logger, router: UrlDispatcher | None = None,
                 middlewares: Iterable[_Middleware] = (),
                 handler_args: Mapping[str, Any] | None = None, client_max_size: int = 1024 ** 2,
                 loop: AbstractEventLoop | None = None, debug: Any = ...) -> None:
        super().__init__(logger=logger, router=router,
                         middlewares=middlewares, handler_args=handler_args,
                         client_max_size=client_max_size, loop=loop, debug=debug)
        self.pm = project_manager
        self.port = port
        self.base_path = base_path