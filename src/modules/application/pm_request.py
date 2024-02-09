from typing import Any

from aiohttp.web import Request

from .pm_application import PMApplication

class PMRequest(Request):
    
    """Класс aiohttp реквеста, свойство app возвращает `PMApplication`"""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.app: PMApplication