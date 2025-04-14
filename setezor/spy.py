import json
import os
from typing import Any, Generic, Literal, Callable, ParamSpec, TypeVar
import inspect
from setezor.settings import PATH_PREFIX
from fastapi import FastAPI, Request, Response
from setezor.logger import logger
_P = ParamSpec("_P")
_Returns = TypeVar("_Returns")


class SpyMethod(Generic[_P, _Returns]):
    def __init__(self, func: Callable[_P, _Returns], endpoint: str, method: Literal['GET', 'POST']) -> None:
        if not self.is_valid(func):
            raise SyntaxError("Annotate all variables and output")
        self._func = func
        self.endpoint: str = endpoint
        self.method: str = method

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _Returns:
        return self._func(*args, **kwargs)
    
    @staticmethod
    def is_valid(func: Callable[_P, _Returns]):
        if not func.__annotations__.get('return'):
            raise SyntaxError(f"Return is not annotated in {func.__name__}")
        annotated_params = set([k for k in func.__annotations__.keys() if k != 'return'])
        params = set(inspect.signature(func).parameters.keys())
        for param in params:
            if not param in annotated_params and param != 'self':
                raise SyntaxError(f"Parameter < {param} > is not annotated in {func.__name__}")
        return True
        
    def __server_function__(self) -> Callable[[Request], Response]:
        sig = inspect.signature(self._func)
        async def handler(**kwargs):
            result = await self(**kwargs)
            return result
        handler.__signature__ = inspect.Signature(sig.parameters.values())
        return handler


class Spy:
    _funcs: list[SpyMethod] = []
    PARENT_AGENT_URLS = []
    SECRET_KEY: str = ""
    @classmethod
    def spy_func(cls, method: Literal['GET', 'POST'], endpoint: str) -> SpyMethod[_P, _Returns]:
        def wrapper(func: Callable[_P, _Returns]) -> SpyMethod[_P, _Returns]:
            _spy_func = SpyMethod(method=method, endpoint=endpoint, func=func)
            cls._funcs.append(_spy_func)
            return _spy_func
        return wrapper
    
    @classmethod
    def create_app(cls) -> FastAPI:
        cls.from_file()
        app: FastAPI = FastAPI()
        for func in cls._funcs:
            app.add_api_route(
                func.endpoint,
                func.__server_function__(),
                methods=[func.method],
                summary=func._func.__name__
            )    
        
        return app
    
    @classmethod
    def from_file(cls):
        try: 
            with open(os.path.join(PATH_PREFIX, "config.json"), 'r') as f:
                config = json.load(f)
            cls.PARENT_AGENT_URLS = config["parent_agents_urls"]
            cls.SECRET_KEY = config["key"]
        except (FileNotFoundError, KeyError, json.decoder.JSONDecodeError):
            logger.warning("Agent is not connected yet")
